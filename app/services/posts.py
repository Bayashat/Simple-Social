"""Post use-cases: orchestrate media upload, persistence, and authorization."""

import uuid

from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile
from imagekitio import (
    APIConnectionError,
    APIStatusError,
    ImageKitError,
    NotFoundError,
    omit,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import imagekit as ik
from app.core import s3
from app.core.config import get_settings
from app.crud import posts as post_crud
from app.models.posts import Post, PostFileType, PostStorage, safe_upload_basename
from app.models.users import User
from app.schemas import PostListData, PostRead, post_read_from_model


def upload_ui_filename(upload: UploadFile) -> str:
    return safe_upload_basename(upload.filename or "upload")


async def _imagekit_delete_file(file_id: str) -> None:
    try:
        await ik.async_imagekit.files.delete(file_id)
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
            await _imagekit_delete_file(post.imagekit_file_id)
    elif post.storage == PostStorage.S3 and post.s3_bucket and post.s3_object_key:
        try:
            await s3.delete_object(bucket=post.s3_bucket, object_key=post.s3_object_key)
        except ClientError as exc:
            raise HTTPException(
                status_code=502,
                detail="Failed to delete object from S3",
            ) from exc


async def upload_new_post(
    session: AsyncSession,
    user: User,
    *,
    payload: bytes,
    content_type: str | None,
    file_name_ui: str,
    caption: str,
    storage: PostStorage,
) -> PostRead:
    trimmed_caption = caption.strip()
    settings = get_settings()

    if storage == PostStorage.S3:
        try:
            obj_key, public_url = await s3.upload_bytes(
                original_filename=file_name_ui,
                body=payload,
                content_type=content_type,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ClientError:
            raise HTTPException(status_code=502, detail="S3 upload failed") from None

        post = Post(
            user_id=user.id,
            caption=trimmed_caption or None,
            storage=PostStorage.S3,
            imagekit_file_id=None,
            s3_bucket=settings.aws_s3_bucket,
            s3_object_key=obj_key,
            url=public_url,
            file_type=PostFileType.from_upload(content_type, None),
            file_name=file_name_ui,
        )
        created = await post_crud.create_post(session, post)
        return post_read_from_model(created, viewer_id=user.id, owner_email=user.email)

    description = trimmed_caption if trimmed_caption else omit

    try:
        ik_resp = await ik.async_imagekit.files.upload(
            file=payload,
            file_name=file_name_ui,
            folder=ik.IMAGEKIT_UPLOAD_FOLDER,
            use_unique_file_name=True,
            description=description,
        )
    except APIStatusError as exc:
        if 400 <= exc.status_code < 500:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
        raise HTTPException(status_code=502, detail="ImageKit upload failed") from exc
    except APIConnectionError as exc:
        raise HTTPException(status_code=503, detail="ImageKit unavailable") from exc
    except ImageKitError as exc:
        raise HTTPException(status_code=502, detail="ImageKit error") from exc

    if not ik_resp.url:
        raise HTTPException(status_code=502, detail="ImageKit returned no file URL")
    if not ik_resp.file_id:
        raise HTTPException(status_code=502, detail="ImageKit returned no file_id")

    post = Post(
        user_id=user.id,
        caption=trimmed_caption or None,
        storage=PostStorage.IMAGEKIT,
        imagekit_file_id=ik_resp.file_id,
        s3_bucket=None,
        s3_object_key=None,
        url=ik_resp.url,
        file_type=PostFileType.from_upload(content_type, ik_resp.file_type),
        file_name=ik_resp.name or file_name_ui,
    )
    created = await post_crud.create_post(session, post)
    return post_read_from_model(created, viewer_id=user.id, owner_email=user.email)


async def list_posts(session: AsyncSession, user: User) -> PostListData:
    rows = await post_crud.list_posts_for_feed(session)
    return PostListData(
        posts=[
            post_read_from_model(
                row,
                viewer_id=user.id,
                owner_email=row.user.email if row.user is not None else "",
            )
            for row in rows
        ]
    )


async def delete_owned_post(
    session: AsyncSession,
    user: User,
    post_id: uuid.UUID,
) -> dict[str, str | bool]:
    existing = await post_crud.get_post_by_id(session, post_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    await delete_post_remote_files(existing)
    await post_crud.delete_post(session, existing)
    return {"success": True, "message": "Post deleted successfully"}
