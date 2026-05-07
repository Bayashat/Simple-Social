"""S3 uploads via boto3 in a thread (does not block the event loop).

Objects created with PutObject are **private by default**. To open the returned HTTPS URL in a
browser without signing in you must grant anonymous ``s3:GetObject`` — typically with a **bucket
policy** (recommended) or optionally ``ACL=public-read`` on each object **only if** your bucket
still allows ACLs (often disabled).

See AWS: https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteAccessPermissionsReqd.html
"""

from __future__ import annotations

import asyncio
from typing import Any
from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.models.posts import safe_upload_basename


def _s3_settings() -> tuple[str | None, str, str, str | None, str | None, str]:
    s = get_settings()
    raw_prefix = s.s3_key_prefix.strip().strip("/")
    return (
        s.aws_s3_bucket,
        s.aws_region,
        f"{raw_prefix}/",
        s.aws_endpoint_url,
        s.s3_public_base_url,
        s.s3_object_acl,
    )


def _client() -> Any:
    _, region, _, endpoint_url, _, _ = _s3_settings()
    kwargs: dict[str, Any] = {"region_name": region}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.client("s3", **kwargs)


def _put_object_sync(
    key: str,
    body: bytes,
    content_type: str | None,
) -> None:
    bucket, _, _, _, _, acl_raw = _s3_settings()
    if not bucket:
        raise ValueError("Set AWS_S3_BUCKET or S3_BUCKET")

    client = _client()
    extra: dict[str, object] = {"Bucket": bucket, "Key": key, "Body": body}
    if content_type:
        extra["ContentType"] = content_type

    acl = acl_raw.strip()
    if acl:
        extra["ACL"] = acl

    client.put_object(**extra)


def _delete_object_sync(bucket: str, key: str) -> None:
    _client().delete_object(Bucket=bucket, Key=key)


def public_object_url(object_key: str) -> str:
    bucket, region, _, _, base_raw, _ = _s3_settings()
    encoded = quote(object_key, safe="/")
    base = (base_raw or "").strip().rstrip("/")
    if base:
        return f"{base}/{encoded}"

    bucket_name = bucket or ""
    if region == "us-east-1":
        host = "s3.amazonaws.com"
        return f"https://{bucket_name}.{host}/{encoded}"
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{encoded}"


async def upload_bytes(
    *,
    original_filename: str,
    body: bytes,
    content_type: str | None,
) -> tuple[str, str]:
    """Upload to S3. Returns (object_key, public_https_url_as_configured)."""
    _, _, key_prefix, _, _, _ = _s3_settings()
    name = safe_upload_basename(original_filename)
    key = f"{key_prefix}{name}"

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
