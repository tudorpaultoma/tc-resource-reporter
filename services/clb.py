"""
CLB Scanner — list all CLB instances and extract tag metadata.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_clb(region, cred):
    """Return list[dict] of CLB records with tag data."""
    from tencentcloud.clb.v20180317 import clb_client, models

    from index import make_tc_client

    client = make_tc_client(clb_client.ClbClient, region, cred)
    resources = []
    offset = 0
    limit = 100

    while True:
        try:
            req = models.DescribeLoadBalancersRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeLoadBalancers(req)
            lbs = resp.LoadBalancerSet or []
        except Exception as exc:
            logger.error("clb scan %s offset=%d: %s", region, offset, exc)
            break

        for lb in lbs:
            tags = {t.TagKey: t.TagValue for t in (lb.Tags or [])}
            # CLB Status is numeric: 1 = active, 0 = not created
            raw_status = lb.Status
            if raw_status == 1:
                state = "ACTIVE"
            elif raw_status == 0:
                state = "CREATING"
            else:
                state = str(raw_status) if raw_status is not None else ""
            resources.append({
                "service": "clb",
                "resource_id": lb.LoadBalancerId,
                "resource_name": lb.LoadBalancerName or "",
                "region": region,
                "state": state,
                "created_time": lb.CreateTime or "",
                "TaggerOwner": tags.get("TaggerOwner", ""),
                "TaggerCreated": tags.get("TaggerCreated", ""),
                "TaggerTTL": tags.get("TaggerTTL", ""),
                "TaggerCanDelete": tags.get("TaggerCanDelete", ""),
                "TaggerProject": tags.get("TaggerProject", ""),
                "TaggerAutoOff": "",
                "TaggerAutoStart": "",
            })

        if len(lbs) < limit:
            break
        offset += limit

    return resources
