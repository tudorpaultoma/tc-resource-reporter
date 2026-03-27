"""
CBS Snapshot Scanner — list all CBS snapshots and extract tag metadata.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_snapshots(region, cred):
    """Return list[dict] of CBS snapshot records with tag data."""
    from tencentcloud.cbs.v20170312 import cbs_client, models

    from index import make_tc_client

    client = make_tc_client(cbs_client.CbsClient, region, cred)
    resources = []
    offset = 0
    limit = 100

    while True:
        try:
            req = models.DescribeSnapshotsRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeSnapshots(req)
            snaps = resp.SnapshotSet or []
        except Exception as exc:
            logger.error("snapshot scan %s offset=%d: %s", region, offset, exc)
            break

        for s in snaps:
            tags = {t.Key: t.Value for t in (s.Tags or [])}
            resources.append({
                "service": "snapshot",
                "resource_id": s.SnapshotId,
                "resource_name": s.SnapshotName or "",
                "region": region,
                "state": s.SnapshotState or "",
                "created_time": s.CreateTime or "",
                "TaggerOwner": tags.get("TaggerOwner", ""),
                "TaggerCreated": tags.get("TaggerCreated", ""),
                "TaggerTTL": tags.get("TaggerTTL", ""),
                "TaggerCanDelete": tags.get("TaggerCanDelete", ""),
                "TaggerProject": tags.get("TaggerProject", ""),
                "TaggerAutoOff": "",
                "TaggerAutoStart": "",
            })

        if len(snaps) < limit:
            break
        offset += limit

    return resources
