"""
services/storage.py
S3-compatible object storage utility. Works with AWS S3, Cloudflare R2,
or local MinIO depending on the env vars you provide.
"""
import os
import uuid
import json
import asyncio
import logging
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

logger = logging.getLogger("storage")

BUCKET_NAME = os.getenv("STORAGE_BUCKET_NAME", "my-ai-app-bucket")
ENDPOINT_URL = os.getenv("STORAGE_ENDPOINT_URL") or None
REGION = os.getenv("STORAGE_REGION", "us-east-1")

# PUBLIC_BASE_URL lets you override how URLs are constructed, which matters
# because R2 buckets need a custom public domain (or signed URLs) - the raw
# endpoint_url is not browser-accessible by default.
PUBLIC_BASE_URL = os.getenv("STORAGE_PUBLIC_BASE_URL")

# Set to "true" when pointing at a local MinIO container (no cloud account
# needed). This flag tells startup code to auto-create the bucket and make
# it public-read, since there's no MinIO web console wizard doing that for
# you the way Cloudflare/AWS dashboards do.
AUTO_PROVISION_BUCKET = os.getenv("STORAGE_AUTO_PROVISION_BUCKET", "false").lower() == "true"

# Explicit connect/read timeouts are critical here: boto3 has no timeout by
# default, so a misconfigured or unreachable endpoint could otherwise hang
# the calling coroutine (and, since put_object is a blocking call, the whole
# event loop) indefinitely.
s3_client = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=os.getenv("STORAGE_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("STORAGE_SECRET_KEY"),
    region_name=REGION,
    config=Config(
        signature_version="s3v4",
        connect_timeout=10,
        read_timeout=30,
        retries={"max_attempts": 2},
    ),
)


def ensure_bucket_exists_and_public() -> None:
    """
    Called once on backend startup when STORAGE_AUTO_PROVISION_BUCKET=true
    (i.e. local MinIO setups with no cloud dashboard to click through).
    Creates the bucket if missing and applies a public-read policy so
    generated image URLs are directly viewable in a browser - mirroring
    what R2's "Public Access" toggle or an S3 public-read bucket policy
    would do.
    """
    if not AUTO_PROVISION_BUCKET:
        return

    try:
        s3_client.head_bucket(Bucket=BUCKET_NAME)
        logger.info("Bucket '%s' already exists.", BUCKET_NAME)
    except ClientError:
        logger.info("Bucket '%s' not found, creating it now.", BUCKET_NAME)
        s3_client.create_bucket(Bucket=BUCKET_NAME)

    public_read_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{BUCKET_NAME}/*"],
            }
        ],
    }
    try:
        s3_client.put_bucket_policy(Bucket=BUCKET_NAME, Policy=json.dumps(public_read_policy))
        logger.info("Public-read policy applied to bucket '%s'.", BUCKET_NAME)
    except ClientError as exc:
        logger.warning("Could not set public-read policy on '%s': %s", BUCKET_NAME, exc)


def _build_public_url(key: str) -> str:
    if PUBLIC_BASE_URL:
        return f"{PUBLIC_BASE_URL.rstrip('/')}/{key}"
    if ENDPOINT_URL:
        # R2 / MinIO style: endpoint already includes scheme+host
        return f"{ENDPOINT_URL.rstrip('/')}/{BUCKET_NAME}/{key}"
    # Standard AWS S3 virtual-hosted-style URL
    return f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{key}"


def _put_object_sync(key: str, file_bytes: bytes, content_type: str) -> None:
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )


async def upload_image_to_storage(file_bytes: bytes, content_type: str, extension: str = "png") -> str:
    """
    Uploads raw image bytes to the configured bucket under a random key
    and returns a public URL pointing at the object.

    boto3 is synchronous/blocking under the hood, so we run the actual
    network call in a thread pool executor via asyncio.to_thread. Calling
    it directly inside this async function would otherwise block the
    entire FastAPI event loop for the duration of the upload.
    """
    key = f"images/{uuid.uuid4()}.{extension}"
    try:
        await asyncio.to_thread(_put_object_sync, key, file_bytes, content_type)
    except Exception as exc:
        raise RuntimeError(f"Failed to upload to object storage: {exc}") from exc
    return _build_public_url(key)


def generate_presigned_get_url(key: str, expires_in: int = 3600) -> str:
    """Useful if your bucket is private rather than public-read."""
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
    )
