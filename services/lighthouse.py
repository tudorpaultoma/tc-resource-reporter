"""
Lighthouse Scanner — list Lighthouse instances and snapshots, extract tag metadata.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_lighthouse(region, cred):
    """Return list[dict] of Lighthouse instance + snapshot records with tag data."""
    from tencentcloud.lighthouse.v20200324 import lighthouse_client, models

    from index import make_tc_client

    client = make_tc_client(lighthouse_client.LighthouseClient, region, cred)
    resources = []

    # --- Instances ---
    offset = 0
    limit = 100
    while True:
        try:
            req = models.DescribeInstancesRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeInstances(req)
            instances = resp.InstanceSet or []
        except Exception as exc:
            logger.error("lighthouse scan %s offset=%d: %s", region, offset, exc)
            break

        for inst in instances:
            tags = {t.Key: t.Value for t in (inst.Tags or [])}
            resources.append({
                "service": "lighthouse",
                "resource_id": inst.InstanceId,
                "resource_name": inst.InstanceName or "",
                "region": region,
                "state": inst.InstanceState or "",
                "created_time": inst.CreatedTime or "",
                "TaggerOwner": tags.get("TaggerOwner", ""),
                "TaggerCreated": tags.get("TaggerCreated", ""),
                "TaggerTTL": tags.get("TaggerTTL", ""),
                "TaggerCanDelete": tags.get("TaggerCanDelete", ""),
                "TaggerProject": tags.get("TaggerProject", ""),
                "TaggerAutoOff": tags.get("TaggerAutoOff", ""),
                "TaggerAutoStart": tags.get("TaggerAutoStart", ""),
            })

        if len(instances) < limit:
            break
        offset += limit

    # --- Snapshots ---
    offset = 0
    while True:
        try:
            req = models.DescribeSnapshotsRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeSnapshots(req)
            snaps = resp.SnapshotSet or []
        except Exception as exc:
            logger.error("lighthouse snapshot scan %s offset=%d: %s", region, offset, exc)
            break

        for s in snaps:
            resources.append({
                "service": "lighthouse_snapshot",
                "resource_id": s.SnapshotId,
                "resource_name": s.SnapshotName or "",
                "region": region,
                "state": s.SnapshotState or "",
                "created_time": s.CreatedTime or "",
                "TaggerOwner": "",
                "TaggerCreated": "",
                "TaggerTTL": "",
                "TaggerCanDelete": "",
                "TaggerProject": "",
                "TaggerAutoOff": "",
                "TaggerAutoStart": "",
            })

        if len(snaps) < limit:
            break
        offset += limit

    return resources
