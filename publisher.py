"""
COS Publisher — uploads the generated HTML report to a COS bucket.
"""

import logging
import os

logger = logging.getLogger("tc-resource-reporter")


def upload_to_cos(html_content: str):
    """Upload *html_content* to the configured COS bucket."""
    from qcloud_cos import CosConfig, CosS3Client

    sid = os.environ.get("TENCENTCLOUD_SECRETID") or os.environ.get("TENCENTCLOUD_SECRET_ID", "")
    skey = os.environ.get("TENCENTCLOUD_SECRETKEY") or os.environ.get("TENCENTCLOUD_SECRET_KEY", "")
    token = os.environ.get("TENCENTCLOUD_SESSIONTOKEN") or os.environ.get("TENCENTCLOUD_SESSION_TOKEN", "")

    bucket = os.environ.get("COS_REPORT_BUCKET", "").strip()
    region = os.environ.get("COS_REPORT_REGION", "").strip()
    key = os.environ.get("COS_REPORT_KEY", "index.html").strip()

    # Strip any path accidentally included in the bucket name
    if "/" in bucket:
        parts = bucket.split("/", 1)
        bucket = parts[0]
        # If user put path in bucket, use it as the key prefix
        if parts[1]:
            key = parts[1].rstrip("/") + "/" + key if not parts[1].endswith(key) else parts[1]
        logger.warning("COS_REPORT_BUCKET contained a path — split into bucket=%s key=%s", bucket, key)

    if not bucket or not region:
        raise RuntimeError(
            "COS_REPORT_BUCKET and COS_REPORT_REGION must be set. "
            "COS_REPORT_BUCKET = bucket name only (e.g. 'my-reports-1234567890'), "
            "COS_REPORT_KEY = object path (default: 'index.html')"
        )

    config = CosConfig(
        Region=region,
        SecretId=sid,
        SecretKey=skey,
        Token=token,
        Scheme="https",
    )
    client = CosS3Client(config)

    body = html_content.encode("utf-8")
    resp = client.put_object(
        Bucket=bucket,
        Body=body,
        Key=key,
        ContentType="text/html; charset=utf-8",
        CacheControl="no-cache",
    )
    logger.info("Uploaded %s to %s/%s  (ETag: %s)", key, bucket, region, resp.get("ETag", "n/a"))
    return resp
