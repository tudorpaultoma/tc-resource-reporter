"""
Auto Scaling Scanner — list all AS groups and launch configs, extract tag metadata.
"""

import logging

logger = logging.getLogger("tc-resource-reporter")


def scan_autoscaling(region, cred):
    """Return list[dict] of AS group + launch config records with tag data."""
    from tencentcloud.autoscaling.v20180419 import autoscaling_client as as_client, models

    from index import make_tc_client

    client = make_tc_client(as_client.AutoscalingClient, region, cred)
    resources = []

    # --- Auto Scaling Groups ---
    offset = 0
    limit = 100
    while True:
        try:
            req = models.DescribeAutoScalingGroupsRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeAutoScalingGroups(req)
            groups = resp.AutoScalingGroupSet or []
        except Exception as exc:
            logger.error("asg scan %s offset=%d: %s", region, offset, exc)
            break

        for g in groups:
            tags = {t.Key: t.Value for t in (g.Tags or [])}
            resources.append({
                "service": "asg",
                "resource_id": g.AutoScalingGroupId,
                "resource_name": g.AutoScalingGroupName or "",
                "region": region,
                "state": g.AutoScalingGroupStatus or "",
                "created_time": g.CreatedTime or "",
                "TaggerOwner": tags.get("TaggerOwner", ""),
                "TaggerCreated": tags.get("TaggerCreated", ""),
                "TaggerTTL": tags.get("TaggerTTL", ""),
                "TaggerCanDelete": tags.get("TaggerCanDelete", ""),
                "TaggerProject": tags.get("TaggerProject", ""),
                "TaggerAutoOff": "",
                "TaggerAutoStart": "",
            })

        if len(groups) < limit:
            break
        offset += limit

    # --- Launch Configurations ---
    offset = 0
    while True:
        try:
            req = models.DescribeLaunchConfigurationsRequest()
            req.Offset = offset
            req.Limit = limit
            resp = client.DescribeLaunchConfigurations(req)
            configs = resp.LaunchConfigurationSet or []
        except Exception as exc:
            logger.error("lc scan %s offset=%d: %s", region, offset, exc)
            break

        for lc in configs:
            tags = {t.Key: t.Value for t in (lc.Tags or [])} if hasattr(lc, "Tags") and lc.Tags else {}
            resources.append({
                "service": "launch_config",
                "resource_id": lc.LaunchConfigurationId,
                "resource_name": lc.LaunchConfigurationName or "",
                "region": region,
                "state": "ACTIVE",
                "created_time": lc.CreatedTime or "",
                "TaggerOwner": tags.get("TaggerOwner", ""),
                "TaggerCreated": tags.get("TaggerCreated", ""),
                "TaggerTTL": tags.get("TaggerTTL", ""),
                "TaggerCanDelete": tags.get("TaggerCanDelete", ""),
                "TaggerProject": tags.get("TaggerProject", ""),
                "TaggerAutoOff": "",
                "TaggerAutoStart": "",
            })

        if len(configs) < limit:
            break
        offset += limit

    return resources
