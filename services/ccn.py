"""
CCN Scanner — list all Cloud Connect Networks and extract tag metadata.
CCN is a global service — scanned once regardless of region.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_ccn(region, cred):
    """Return list[dict] of CCN records with tag data."""
    from tencentcloud.vpc.v20170312 import vpc_client, models

    from index import make_tc_client

    client = make_tc_client(vpc_client.VpcClient, region, cred)
    resources = []
    offset = 0
    limit = 100

    while True:
        try:
            req = models.DescribeCcnsRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeCcns(req)
            ccns = resp.CcnSet or []
        except Exception as exc:
            logger.error("ccn scan %s offset=%d: %s", region, offset, exc)
            break

        for c in ccns:
            tags = {t.Key: t.Value for t in (c.TagSet or [])}
            resources.append({
                "service": "ccn",
                "resource_id": c.CcnId,
                "resource_name": c.CcnName or "",
                "region": "global",
                "state": c.State or "",
                "created_time": c.CreateTime or "",
                "TaggerOwner": tags.get("TaggerOwner", ""),
                "TaggerCreated": tags.get("TaggerCreated", ""),
                "TaggerTTL": tags.get("TaggerTTL", ""),
                "TaggerCanDelete": tags.get("TaggerCanDelete", ""),
                "TaggerProject": tags.get("TaggerProject", ""),
                "TaggerAutoOff": "",
                "TaggerAutoStart": "",
            })

        if len(ccns) < limit:
            break
        offset += limit

    return resources
