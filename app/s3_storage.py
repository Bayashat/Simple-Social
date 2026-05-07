"""S3 uploads via boto3 in a thread (does not block the event loop).

Objects created with PutObject are **private by default**. To open the returned HTTPS URL in a
browser without signing in you must grant anonymous ``s3:GetObject`` — typically with a **bucket
policy** (recommended) or optionally ``ACL=public-read`` on each object **only if** your bucket
still allows ACLs (often disabled).

See AWS: https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteAccessPermissionsReqd.html
"""

from __future__ import annotations

import asyncio
import os
from typing import Any
from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError

from app.models.posts import safe_upload_basename

s3_bucket_name = os.environ.get("AWS_S3_BUCKET") or os.environ.get("S3_BUCKET")
s3_region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
_raw_prefix = (os.environ.get("S3_KEY_PREFIX") or "posts").strip().strip("/")
s3_key_prefix = f"{_raw_prefix}/"


def _client() -> Any:
    kwargs: dict[str, Any] = {"region_name": s3_region}
    ep = os.environ.get("AWS_ENDPOINT_URL") or os.environ.get("S3_ENDPOINT_URL")
    if ep:
        kwargs["endpoint_url"] = ep
    return boto3.client("s3", **kwargs)


def _put_object_sync(
    key: str,
    body: bytes,
    content_type: str | None,
) -> None:
    if not s3_bucket_name:
        raise ValueError("Set AWS_S3_BUCKET or S3_BUCKET")

    client = _client()
    extra: dict[str, object] = {"Bucket": s3_bucket_name, "Key": key, "Body": body}
    if content_type:
        extra["ContentType"] = content_type

    acl = (os.environ.get("S3_OBJECT_ACL") or "").strip()
    if acl:
        extra["ACL"] = acl

    client.put_object(**extra)


def _delete_object_sync(bucket: str, key: str) -> None:
    _client().delete_object(Bucket=bucket, Key=key)


def public_object_url(object_key: str) -> str:
    encoded = quote(object_key, safe="/")
    base = (os.environ.get("S3_PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if base:
        return f"{base}/{encoded}"

    bn = s3_bucket_name or ""
    if s3_region == "us-east-1":
        host = "s3.amazonaws.com"
        return f"https://{bn}.{host}/{encoded}"
    return f"https://{bn}.s3.{s3_region}.amazonaws.com/{encoded}"


async def upload_bytes(
    *,
    original_filename: str,
    body: bytes,
    content_type: str | None,
) -> tuple[str, str]:
    """Upload to S3. Returns (object_key, public_https_url_as_configured).

    Opening that URL anonymously requires IAM/bucket-side public read configuration.
    """
    name = safe_upload_basename(original_filename)
    key = f"{s3_key_prefix}{name}"

    await asyncio.to_thread(_put_object_sync, key, body, content_type)
    return key, public_object_url(key)


async def delete_object(*, bucket: str, object_key: str) -> None:
    """Delete object; treats missing key as success."""

    def _run() -> None:
        try:
            _delete_object_sync(bucket, object_key)
        except ClientError as exc:
            code = (exc.response.get("Error") or {}).get("Code", "")
            if code in ("404", "NoSuchKey", "NotFound"):
                return
            raise

    await asyncio.to_thread(_run)
