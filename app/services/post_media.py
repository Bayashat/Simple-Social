from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile
from imagekitio import (
    APIConnectionError,
    APIStatusError,
    ImageKitError,
    NotFoundError,
)

from app.images import async_imagekit
from app.models.posts import Post, PostStorage, safe_upload_basename
from app.s3_storage import delete_object as s3_delete_object


def upload_ui_filename(upload: UploadFile) -> str:
    return safe_upload_basename(upload.filename or "upload")


async def imagekit_delete_file(file_id: str) -> None:
    """Remove asset from ImageKit media library (idempotent when already gone)."""
    try:
        await async_imagekit.files.delete(file_id)
    except NotFoundError:
        return
    except APIStatusError as exc:
        if exc.status_code == 404:
            return
        if 400 <= exc.status_code < 500:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
        raise HTTPException(status_code=502, detail="ImageKit delete failed") from exc
    except APIConnectionError as exc:
        raise HTTPException(status_code=503, detail="ImageKit unavailable") from exc
    except ImageKitError as exc:
        raise HTTPException(status_code=502, detail="ImageKit error") from exc


async def delete_post_remote_files(post: Post) -> None:
    if post.storage == PostStorage.IMAGEKIT:
        if post.imagekit_file_id:
            await imagekit_delete_file(post.imagekit_file_id)
    elif post.storage == PostStorage.S3 and post.s3_bucket and post.s3_object_key:
        try:
            await s3_delete_object(bucket=post.s3_bucket, object_key=post.s3_object_key)
        except ClientError as exc:
            raise HTTPException(
                status_code=502,
                detail="Failed to delete object from S3",
            ) from exc
