"""
COS Publisher — uploads the login page and hashed report to a COS bucket.

The login page is always uploaded as ``index.html``.
The report is uploaded as ``report_<sha256>.html`` where the hash is derived
from the credentials so the URL is unguessable.
"""

import logging
import os

logger = logging.getLogger("tc-resource-reporter")


def _cos_client():
    """Build and return a CosS3Client from SCF env vars."""
    from qcloud_cos import CosConfig, CosS3Client

    sid = os.environ.get("TENCENTCLOUD_SECRETID") or os.environ.get("TENCENTCLOUD_SECRET_ID", "")
    skey = os.environ.get("TENCENTCLOUD_SECRETKEY") or os.environ.get("TENCENTCLOUD_SECRET_KEY", "")
    token = os.environ.get("TENCENTCLOUD_SESSIONTOKEN") or os.environ.get("TENCENTCLOUD_SESSION_TOKEN", "")
    region = os.environ.get("COS_REPORT_REGION", "").strip()

    config = CosConfig(
        Region=region,
        SecretId=sid,
        SecretKey=skey,
        Token=token,
        Scheme="https",
    )
    return CosS3Client(config), region


def _get_bucket():
    """Return sanitised bucket name and base key prefix.

    The prefix is derived from COS_REPORT_KEY (directory portion) or, as a
    fallback, from a ``/`` in COS_REPORT_BUCKET (legacy behaviour).

    Examples:
        COS_REPORT_KEY=/Report/index.html  →  prefix = "Report/"
        COS_REPORT_KEY=index.html           →  prefix = ""
        COS_REPORT_KEY not set, bucket has / →  legacy split
    """
    bucket = os.environ.get("COS_REPORT_BUCKET", "").strip()
    prefix = ""

    # --- derive prefix from COS_REPORT_KEY (preferred) ---
    report_key = os.environ.get("COS_REPORT_KEY", "").strip().lstrip("/")
    if report_key:
        # Take the directory part: "Report/index.html" → "Report/"
        if "/" in report_key:
            prefix = report_key.rsplit("/", 1)[0].rstrip("/") + "/"
        # else: key is just a filename like "index.html" → no prefix
        logger.info("Derived upload prefix from COS_REPORT_KEY: '%s'", prefix)

    # --- legacy fallback: path embedded in COS_REPORT_BUCKET ---
    if not prefix and "/" in bucket:
        parts = bucket.split("/", 1)
        bucket = parts[0]
        if parts[1]:
            prefix = parts[1].rstrip("/") + "/"
        logger.warning("COS_REPORT_BUCKET contained a path — split into bucket=%s prefix=%s", bucket, prefix)

    region = os.environ.get("COS_REPORT_REGION", "").strip()
    if not bucket or not region:
        raise RuntimeError(
            "COS_REPORT_BUCKET and COS_REPORT_REGION must be set. "
            "COS_REPORT_BUCKET = bucket name only (e.g. 'my-reports-1234567890')"
        )
    return bucket, prefix


def _put(client, bucket, key, body_str):
    """Upload a UTF-8 HTML string to COS with correct Content-Type."""
    resp = client.put_object(
        Bucket=bucket,
        Body=body_str.encode("utf-8"),
        Key=key,
        ContentType="text/html; charset=utf-8",
        ContentDisposition="inline",
        CacheControl="no-cache",
    )
    logger.info("Uploaded %s  (ETag: %s)", key, resp.get("ETag", "n/a"))
    return resp


def _cleanup_old_reports(client, bucket, prefix, current_report_key):
    """Delete any previous report_*.html files that don't match the current hash."""
    try:
        marker = ""
        while True:
            resp = client.list_objects(
                Bucket=bucket,
                Prefix=prefix + "report_",
                Marker=marker,
                MaxKeys=100,
            )
            contents = resp.get("Contents", [])
            if not contents:
                break
            for obj in contents:
                key = obj["Key"]
                if key != current_report_key and key.endswith(".html"):
                    client.delete_object(Bucket=bucket, Key=key)
                    logger.info("Deleted old report: %s", key)
            if resp.get("IsTruncated") == "true":
                marker = resp.get("NextMarker", "")
            else:
                break
    except Exception as exc:
        logger.warning("Cleanup of old reports failed (non-fatal): %s", exc)


def upload_to_cos(*, login_html: str, report_html: str, report_hash: str):
    """Upload login page (index.html) and report (report_<hash>.html) to COS.

    Also cleans up old report files whose hash no longer matches.
    """
    client, region = _cos_client()
    bucket, prefix = _get_bucket()

    login_key = prefix + "index.html"
    report_key = prefix + f"report_{report_hash}.html"

    _put(client, bucket, login_key, login_html)
    _put(client, bucket, report_key, report_html)

    # Remove old report files from previous credential hashes
    _cleanup_old_reports(client, bucket, prefix, report_key)

    logger.info("Published to %s/%s  (report key: %s)", bucket, region, report_key)
    return {"login_key": login_key, "report_key": report_key}
