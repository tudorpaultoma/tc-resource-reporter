"""
ENI Scanner — list all Elastic Network Interfaces and extract tag metadata.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_eni(region, cred):
    """Return list[dict] of ENI records with tag data."""
    from tencentcloud.vpc.v20170312 import vpc_client, models

    from index import make_tc_client

    client = make_tc_client(vpc_client.VpcClient, region, cred)
    resources = []
    offset = 0
    limit = 100

    while True:
        try:
            req = models.DescribeNetworkInterfacesRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeNetworkInterfaces(req)
            enis = resp.NetworkInterfaceSet or []
        except Exception as exc:
            logger.error("eni scan %s offset=%d: %s", region, offset, exc)
            break

        for e in enis:
            tags = {t.Key: t.Value for t in (e.TagSet or [])}
            resources.append({
                "service": "eni",
                "resource_id": e.NetworkInterfaceId,
                "resource_name": e.NetworkInterfaceName or "",
                "region": region,
                "state": e.State or "",
                "created_time": e.CreatedTime or "",
                "TaggerOwner": tags.get("TaggerOwner", ""),
                "TaggerCreated": tags.get("TaggerCreated", ""),
                "TaggerTTL": tags.get("TaggerTTL", ""),
                "TaggerCanDelete": tags.get("TaggerCanDelete", ""),
                "TaggerProject": tags.get("TaggerProject", ""),
                "TaggerAutoOff": "",
                "TaggerAutoStart": "",
            })

        if len(enis) < limit:
            break
        offset += limit

    return resources
