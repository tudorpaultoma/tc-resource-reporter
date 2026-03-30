"""
TC Resource Reporter — SCF Handler & Orchestrator
Scans Tencent Cloud resources across regions, collects tag metadata,
generates a static HTML dashboard and uploads it to COS.

Auth: The report is uploaded as report_<sha256>.html where the hash is
derived from credentials stored in credentials.json or env vars.
A login page (index.html) gates access via client-side hash verification.

Author:  Tudor Toma
Version: 1.1.1
License: GPL-3.0
"""

import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# SCF runtime: ensure vendored packages are importable
# ---------------------------------------------------------------------------
for _p in ("/var/user/package", "/opt/python"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tencentcloud.common import credential as tc_credential

from services.cvm import scan_cvm
from services.clb import scan_clb
from services.cbs import scan_cbs
from services.snapshot import scan_snapshots
from services.eip import scan_eip
from services.eni import scan_eni
from services.havip import scan_havip
from services.nat import scan_nat
from services.ccn import scan_ccn
from services.tke import scan_tke
from services.autoscaling import scan_autoscaling
from services.lighthouse import scan_lighthouse

from template import render_report, render_login
from publisher import upload_to_cos

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("tc-resource-reporter")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s"))
    logger.addHandler(_h)

# ---------------------------------------------------------------------------
# Supported regions (same list used by tc-tag-enforcer)
# ---------------------------------------------------------------------------
ALL_REGIONS = [
    "ap-guangzhou", "ap-shanghai", "ap-nanjing", "ap-beijing",
    "ap-chengdu", "ap-chongqing", "ap-hongkong", "ap-singapore",
    "ap-jakarta", "ap-seoul", "ap-tokyo", "ap-bangkok",
    "eu-frankfurt", "na-siliconvalley", "na-ashburn",
]

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
def _cfg_regions():
    raw = os.environ.get("REPORT_REGIONS", "").strip()
    if raw:
        return [r.strip() for r in raw.split(",") if r.strip()]
    return list(ALL_REGIONS)


def _cfg_services():
    raw = os.environ.get("REPORT_SERVICES", "").strip()
    if raw:
        return [s.strip().lower() for s in raw.split(",") if s.strip()]
    return []  # empty = all


EXPIRY_WARNING_DAYS = int(os.environ.get("EXPIRY_WARNING_DAYS", "3"))
TIMEZONE_OFFSET = int(os.environ.get("TIMEZONE_OFFSET", "8"))
REPORT_TITLE = os.environ.get("REPORT_TITLE", "Shared test account — Resource Usage Report")

# ---------------------------------------------------------------------------
# Report credential resolution (for hashed filename auth)
# ---------------------------------------------------------------------------
def _resolve_report_credentials():
    """Return SHA-256 hex digest of 'username:password'.

    Credentials are read from (in priority order):
      1. Environment variables REPORT_USERNAME / REPORT_PASSWORD
      2. credentials.json in the function root
    """
    username = os.environ.get("REPORT_USERNAME", "").strip()
    password = os.environ.get("REPORT_PASSWORD", "").strip()

    if not username or not password:
        # Try loading from credentials.json (bundled in the zip)
        cred_paths = [
            os.path.join(os.path.dirname(__file__), "credentials.json"),
            "/var/user/credentials.json",
        ]
        for p in cred_paths:
            if os.path.isfile(p):
                with open(p, "r") as f:
                    creds = json.load(f)
                username = creds.get("username", "").strip()
                password = creds.get("password", "").strip()
                if username and password:
                    logger.info("Loaded report credentials from %s", p)
                    break

    if not username or not password:
        raise RuntimeError(
            "Report credentials not configured. Set REPORT_USERNAME + REPORT_PASSWORD "
            "env vars, or include credentials.json in the deployment package."
        )

    raw = f"{username}:{password}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

# ---------------------------------------------------------------------------
# Credential resolution (same pattern as sibling repos)
# ---------------------------------------------------------------------------
def _resolve_credentials():
    """Return (secret_id, secret_key, token) from SCF execution-role env."""
    sid = os.environ.get("TENCENTCLOUD_SECRETID") or os.environ.get("TENCENTCLOUD_SECRET_ID", "")
    skey = os.environ.get("TENCENTCLOUD_SECRETKEY") or os.environ.get("TENCENTCLOUD_SECRET_KEY", "")
    token = os.environ.get("TENCENTCLOUD_SESSIONTOKEN") or os.environ.get("TENCENTCLOUD_SESSION_TOKEN", "")
    if not sid or not skey:
        raise RuntimeError("Missing Tencent Cloud credentials. Attach an execution role to the SCF function.")
    return sid, skey, token


def make_tc_client(client_cls, region, cred):
    """Instantiate a Tencent Cloud SDK client (shared helper)."""
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.common.profile.client_profile import ClientProfile

    hp = HttpProfile()
    hp.reqMethod = "POST"
    cp = ClientProfile()
    cp.httpProfile = hp
    return client_cls(cred, region, cp)

# ---------------------------------------------------------------------------
# Service scanner registry
# ---------------------------------------------------------------------------
SERVICE_SCANNERS = {
    "cvm":                scan_cvm,
    "clb":                scan_clb,
    "cbs":                scan_cbs,
    "snapshot":           scan_snapshots,
    "eip":                scan_eip,
    "eni":                scan_eni,
    "havip":              scan_havip,
    "nat":                scan_nat,
    "ccn":                scan_ccn,
    "tke":                scan_tke,
    "autoscaling":        scan_autoscaling,
    "lighthouse":         scan_lighthouse,
}

# CCN is a global service — scan once with first region
GLOBAL_SERVICES = {"ccn"}

# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
def run(regions, services_filter, cred):
    """Scan all regions × services, return list[dict] of resource records."""
    all_resources = []
    global_done = set()

    for region in regions:
        for svc_name, scanner_fn in SERVICE_SCANNERS.items():
            if services_filter and svc_name not in services_filter:
                continue
            if svc_name in GLOBAL_SERVICES:
                if svc_name in global_done:
                    continue
                global_done.add(svc_name)

            try:
                resources = scanner_fn(region, cred)
                all_resources.extend(resources)
                logger.info("%-20s  %-18s  found %d", region, svc_name, len(resources))
            except Exception as exc:
                logger.error("%-20s  %-18s  ERROR: %s", region, svc_name, exc)

    return all_resources

# ---------------------------------------------------------------------------
# Statistics computation
# ---------------------------------------------------------------------------
def compute_stats(resources):
    """Derive summary statistics from the flat resource list."""
    now = datetime.now(tz=timezone.utc)
    warning_cutoff = now + timedelta(days=EXPIRY_WARNING_DAYS)

    stats = {
        "total": len(resources),
        "by_owner": {},
        "by_service": {},
        "by_region": {},
        "by_project": {},
        "expiring_soon": [],
        "already_expired": [],
        "incomplete_tags": [],
        "auto_managed": [],
        "no_delete_no_project": [],
    }

    for r in resources:
        owner = r.get("TaggerOwner", "unknown")
        svc = r.get("service", "unknown")
        region = r.get("region", "unknown")
        project = r.get("TaggerProject", "n/a")

        # by owner
        stats["by_owner"].setdefault(owner, []).append(r)
        # by service
        stats["by_service"][svc] = stats["by_service"].get(svc, 0) + 1
        # by region
        stats["by_region"][region] = stats["by_region"].get(region, 0) + 1
        # by project
        stats["by_project"][project] = stats["by_project"].get(project, 0) + 1

        # --- expiry analysis ---
        created_str = r.get("TaggerCreated", "")
        ttl_str = r.get("TaggerTTL", "")
        can_delete = r.get("TaggerCanDelete", "YES")

        if created_str and ttl_str:
            try:
                from dateutil.parser import parse as dateparse
                created_dt = dateparse(created_str)
                if created_dt.tzinfo is None:
                    created_dt = created_dt.replace(tzinfo=timezone.utc)
                ttl_days = int(ttl_str)
                expires_at = created_dt + timedelta(days=ttl_days)
                r["_expires_at"] = expires_at.isoformat()
                r["_days_left"] = (expires_at - now).days

                if expires_at <= now:
                    stats["already_expired"].append(r)
                elif expires_at <= warning_cutoff:
                    stats["expiring_soon"].append(r)
            except (ValueError, TypeError):
                pass

        # incomplete tags — missing owner or created
        if not r.get("TaggerOwner") or not r.get("TaggerCreated"):
            stats["incomplete_tags"].append(r)

        # no-delete but missing project (at risk of deletion)
        if str(can_delete).upper() == "NO" and not r.get("TaggerProject"):
            stats["no_delete_no_project"].append(r)

        # auto-managed CVMs
        if svc == "cvm" and r.get("TaggerAutoOff") == "YES":
            stats["auto_managed"].append(r)

    # sort expiring_soon by days_left ascending
    stats["expiring_soon"].sort(key=lambda x: x.get("_days_left", 999))
    stats["already_expired"].sort(key=lambda x: x.get("_days_left", 0))

    return stats

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main_handler(event, context):
    """SCF entry point (Timer trigger)."""
    t0 = time.time()
    logger.info("tc-resource-reporter v1.1.1 — starting")

    try:
        # --- Auth: compute report filename hash ---
        report_hash = _resolve_report_credentials()
        logger.info("Report hash prefix: %s...", report_hash[:8])

        sid, skey, token = _resolve_credentials()
        cred = tc_credential.Credential(sid, skey, token)

        regions = _cfg_regions()
        services_filter = _cfg_services()

        logger.info("Regions: %d  |  Services filter: %s", len(regions), services_filter or "ALL")

        resources = run(regions, services_filter, cred)
        stats = compute_stats(resources)

        # timestamp for the report
        tz = timezone(timedelta(hours=TIMEZONE_OFFSET))
        report_ts = datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S %Z")
        elapsed = round(time.time() - t0, 1)

        report_html = render_report(
            title=REPORT_TITLE,
            resources=resources,
            stats=stats,
            report_time=report_ts,
            elapsed=elapsed,
            regions_scanned=len(regions),
            version="1.1.1",
        )

        login_html = render_login(
            title=REPORT_TITLE,
            version="1.1.1",
        )

        upload_to_cos(
            login_html=login_html,
            report_html=report_html,
            report_hash=report_hash,
        )

        summary = {
            "total_resources": stats["total"],
            "expiring_soon": len(stats["expiring_soon"]),
            "already_expired": len(stats["already_expired"]),
            "incomplete_tags": len(stats["incomplete_tags"]),
            "no_delete_no_project": len(stats["no_delete_no_project"]),
            "elapsed_seconds": elapsed,
        }
        logger.info("Done — %s", json.dumps(summary))
        return {"statusCode": 200, "body": summary}

    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
        return {"statusCode": 500, "body": str(exc)}


if __name__ == "__main__":
    run_result = main_handler({}, None)
    print(json.dumps(run_result, indent=2))
