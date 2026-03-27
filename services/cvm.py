"""
CVM Scanner — list all CVM instances and extract tag metadata.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_cvm(region, cred):
    """Return list[dict] of CVM instance records with tag data."""
    from tencentcloud.cvm.v20170312 import cvm_client, models

    from index import make_tc_client

    client = make_tc_client(cvm_client.CvmClient, region, cred)
    resources = []
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
            logger.error("cvm scan %s offset=%d: %s", region, offset, exc)
            break

        for inst in instances:
            tags = {t.Key: t.Value for t in (inst.Tags or [])}
            resources.append({
                "service": "cvm",
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

    return resources
