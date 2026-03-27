"""
NAT Gateway Scanner — list all NAT Gateways and extract tag metadata.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_nat(region, cred):
    """Return list[dict] of NAT Gateway records with tag data."""
    from tencentcloud.vpc.v20170312 import vpc_client, models

    from index import make_tc_client

    client = make_tc_client(vpc_client.VpcClient, region, cred)
    resources = []
    offset = 0
    limit = 100

    while True:
        try:
            req = models.DescribeNatGatewaysRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeNatGateways(req)
            nats = resp.NatGatewaySet or []
        except Exception as exc:
            logger.error("nat scan %s offset=%d: %s", region, offset, exc)
            break

        for n in nats:
            tags = {t.Key: t.Value for t in (n.TagSet or [])}
            resources.append({
                "service": "nat",
                "resource_id": n.NatGatewayId,
                "resource_name": n.NatGatewayName or "",
                "region": region,
                "state": n.State or "",
                "created_time": n.CreatedTime or "",
                "TaggerOwner": tags.get("TaggerOwner", ""),
                "TaggerCreated": tags.get("TaggerCreated", ""),
                "TaggerTTL": tags.get("TaggerTTL", ""),
                "TaggerCanDelete": tags.get("TaggerCanDelete", ""),
                "TaggerProject": tags.get("TaggerProject", ""),
                "TaggerAutoOff": "",
                "TaggerAutoStart": "",
            })

        if len(nats) < limit:
            break
        offset += limit

    return resources
