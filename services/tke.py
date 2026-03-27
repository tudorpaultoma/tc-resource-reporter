"""
TKE Scanner — list all TKE clusters and extract tag metadata.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_tke(region, cred):
    """Return list[dict] of TKE cluster records with tag data."""
    from tencentcloud.tke.v20180525 import tke_client, models

    from index import make_tc_client

    client = make_tc_client(tke_client.TkeClient, region, cred)
    resources = []
    offset = 0
    limit = 100

    while True:
        try:
            req = models.DescribeClustersRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeClusters(req)
            clusters = resp.Clusters or []
        except Exception as exc:
            logger.error("tke scan %s offset=%d: %s", region, offset, exc)
            break

        for cl in clusters:
            tags = {}
            if hasattr(cl, "TagSpecification") and cl.TagSpecification:
                for ts in cl.TagSpecification:
                    if hasattr(ts, "Tags") and ts.Tags:
                        for t in ts.Tags:
                            tags[t.Key] = t.Value

            resources.append({
                "service": "tke",
                "resource_id": cl.ClusterId,
                "resource_name": cl.ClusterName or "",
                "region": region,
                "state": cl.ClusterStatus or "",
                "created_time": cl.CreatedTime or "",
                "TaggerOwner": tags.get("TaggerOwner", ""),
                "TaggerCreated": tags.get("TaggerCreated", ""),
                "TaggerTTL": tags.get("TaggerTTL", ""),
                "TaggerCanDelete": tags.get("TaggerCanDelete", ""),
                "TaggerProject": tags.get("TaggerProject", ""),
                "TaggerAutoOff": "",
                "TaggerAutoStart": "",
            })

        if len(clusters) < limit:
            break
        offset += limit

    return resources
