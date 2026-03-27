"""
CBS Scanner — list all CBS disks and extract tag metadata.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_cbs(region, cred):
    """Return list[dict] of CBS disk records with tag data."""
    from tencentcloud.cbs.v20170312 import cbs_client, models

    from index import make_tc_client

    client = make_tc_client(cbs_client.CbsClient, region, cred)
    resources = []
    offset = 0
    limit = 100

    while True:
        try:
            req = models.DescribeDisksRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeDisks(req)
            disks = resp.DiskSet or []
        except Exception as exc:
            logger.error("cbs scan %s offset=%d: %s", region, offset, exc)
            break

        for d in disks:
            tags = {t.Key: t.Value for t in (d.Tags or [])}
            resources.append({
                "service": "cbs",
                "resource_id": d.DiskId,
                "resource_name": d.DiskName or "",
                "region": region,
                "state": d.DiskState or "",
                "created_time": d.CreateTime or "",
                "TaggerOwner": tags.get("TaggerOwner", ""),
                "TaggerCreated": tags.get("TaggerCreated", ""),
                "TaggerTTL": tags.get("TaggerTTL", ""),
                "TaggerCanDelete": tags.get("TaggerCanDelete", ""),
                "TaggerProject": tags.get("TaggerProject", ""),
                "TaggerAutoOff": "",
                "TaggerAutoStart": "",
            })

        if len(disks) < limit:
            break
        offset += limit

    return resources
