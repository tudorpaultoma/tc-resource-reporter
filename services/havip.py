"""
HAVIP Scanner — list all HA VIPs and extract tag metadata.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_havip(region, cred):
    """Return list[dict] of HAVIP records with tag data."""
    from tencentcloud.vpc.v20170312 import vpc_client, models

    from index import make_tc_client

    client = make_tc_client(vpc_client.VpcClient, region, cred)
    resources = []
    offset = 0
    limit = 100

    while True:
        try:
            req = models.DescribeHaVipsRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeHaVips(req)
            havips = resp.HaVipSet or []
        except Exception as exc:
            logger.error("havip scan %s offset=%d: %s", region, offset, exc)
            break

        for h in havips:
            # HAVIP API does not expose tags directly
            resources.append({
                "service": "havip",
                "resource_id": h.HaVipId,
                "resource_name": h.HaVipName or "",
                "region": region,
                "state": h.State or "",
                "created_time": h.CreatedTime or "",
                "TaggerOwner": "",
                "TaggerCreated": "",
                "TaggerTTL": "",
                "TaggerCanDelete": "",
                "TaggerProject": "",
                "TaggerAutoOff": "",
                "TaggerAutoStart": "",
            })

        if len(havips) < limit:
            break
        offset += limit

    return resources
