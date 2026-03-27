"""
EIP Scanner — list all EIPs and extract tag metadata.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_eip(region, cred):
    """Return list[dict] of EIP records with tag data."""
    from tencentcloud.vpc.v20170312 import vpc_client, models

    from index import make_tc_client

    client = make_tc_client(vpc_client.VpcClient, region, cred)
    resources = []

    try:
        req = models.DescribeAddressesRequest()
        resp = client.DescribeAddresses(req)
        addresses = resp.AddressSet or []
    except Exception as exc:
        logger.error("eip scan %s: %s", region, exc)
        return resources

    for a in addresses:
        tags = {t.Key: t.Value for t in (a.TagSet or [])}
        resources.append({
            "service": "eip",
            "resource_id": a.AddressId,
            "resource_name": a.AddressName or "",
            "region": region,
            "state": a.AddressStatus or "",
            "created_time": a.CreatedTime or "",
            "TaggerOwner": tags.get("TaggerOwner", ""),
            "TaggerCreated": tags.get("TaggerCreated", ""),
            "TaggerTTL": tags.get("TaggerTTL", ""),
            "TaggerCanDelete": tags.get("TaggerCanDelete", ""),
            "TaggerProject": tags.get("TaggerProject", ""),
            "TaggerAutoOff": "",
            "TaggerAutoStart": "",
        })

    return resources
