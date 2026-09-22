# storage.py
import boto3
from botocore.config import Config
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings

s3 = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    region_name=settings.S3_REGION,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_KEY,
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)

MAX_AVATAR_SIZE = settings.MAX_AVATAR_SIZE
MAX_ATTACHMENT_SIZE = settings.MAX_ATTACHMENT_SIZE
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
DANGEROUS_INLINE_TYPES = {
    "text/html",
    "application/xhtml+xml",
    "image/svg+xml",
    "application/xml",
    "text/xml",
    "application/javascript",
    "text/javascript",
    "application/x-javascript",
}

def needs_forced_download(content_type: str) -> bool:
    return content_type in DANGEROUS_INLINE_TYPES

def presign_post(bucket: str, key: str, content_type: str, max_size: int) -> dict:
    return s3.generate_presigned_post(
        Bucket=bucket,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, max_size],
        ],
        ExpiresIn=300,
    )


def presign_get(
    bucket: str,
    key: str,
    filename: str,
    content_type: str,
    expires_in: int = 300,
) -> str:
    from urllib.parse import quote

    disposition = "attachment"
    if content_type.startswith("image/") and not needs_forced_download(content_type):
        disposition = "inline"

    return s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ResponseContentDisposition": f"{disposition}; filename*=UTF-8''{quote(filename)}",
        },
        ExpiresIn=expires_in,
    )


async def head_object(bucket: str, key: str) -> dict | None:
    try:
        return await run_in_threadpool(s3.head_object, Bucket=bucket, Key=key)
    except s3.exceptions.ClientError:
        return None


async def delete_object(bucket: str, key: str) -> None:
    await run_in_threadpool(s3.delete_object, Bucket=bucket, Key=key)
