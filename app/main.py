import uuid
from contextlib import asynccontextmanager

from botocore.exceptions import ClientError
from fastapi import FastAPI, File, Form, HTTPException, Path, UploadFile
from imagekitio import APIConnectionError, APIStatusError, ImageKitError, NotFoundError, omit
from sqlalchemy import select

from app.db import create_db_and_tables
from app.dependencies import SessionDep
from app.images import IMAGEKIT_UPLOAD_FOLDER, async_imagekit
from app.models.posts import Post, PostFileType, PostStorage, safe_upload_basename
from app.s3_storage import delete_object as s3_delete_object
from app.s3_storage import s3_bucket_name, upload_bytes as s3_upload_bytes
from app.schemas import PostListData, PostRead


def _upload_filename(upload: UploadFile) -> str:
    return safe_upload_basename(upload.filename or "upload")


async def _imagekit_delete_file(file_id: str) -> None:
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


async def _delete_post_remote(post: Post) -> None:
    if post.storage == PostStorage.IMAGEKIT:
        if post.imagekit_file_id:
            await _imagekit_delete_file(post.imagekit_file_id)
    elif post.storage == PostStorage.S3:
        if post.s3_bucket and post.s3_object_key:
            try:
                await s3_delete_object(bucket=post.s3_bucket, object_key=post.s3_object_key)
            except ClientError as exc:
                raise HTTPException(
                    status_code=502,
                    detail="Failed to delete object from S3",
                ) from exc


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    await async_imagekit.close()


app = FastAPI(lifespan=lifespan)


@app.post("/upload", response_model=PostRead)
async def upload_file(
    session: SessionDep,
    file: UploadFile = File(...),
    caption: str = Form(""),
    storage: PostStorage = Form(PostStorage.IMAGEKIT),
) -> PostRead:
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty file")

    trimmed_caption = caption.strip()
    file_name_ui = _upload_filename(file)

    if storage == PostStorage.S3:
        try:
            obj_key, public_url = await s3_upload_bytes(
                original_filename=file_name_ui,
                body=payload,
                content_type=file.content_type,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ClientError:
            raise HTTPException(status_code=502, detail="S3 upload failed") from None

        post = Post(
            caption=trimmed_caption or None,
            storage=PostStorage.S3,
            imagekit_file_id=None,
            s3_bucket=s3_bucket_name,
            s3_object_key=obj_key,
            url=public_url,
            file_type=PostFileType.from_upload(file.content_type, None),
            file_name=file_name_ui,
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post

    # ImageKit path
    description = trimmed_caption if trimmed_caption else omit

    try:
        ik = await async_imagekit.files.upload(
            file=payload,
            file_name=file_name_ui,
            folder=IMAGEKIT_UPLOAD_FOLDER,
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

    if not ik.url:
        raise HTTPException(status_code=502, detail="ImageKit returned no file URL")
    if not ik.file_id:
        raise HTTPException(status_code=502, detail="ImageKit returned no file_id")

    post = Post(
        caption=trimmed_caption or None,
        storage=PostStorage.IMAGEKIT,
        imagekit_file_id=ik.file_id,
        s3_bucket=None,
        s3_object_key=None,
        url=ik.url,
        file_type=PostFileType.from_upload(file.content_type, ik.file_type),
        file_name=ik.name or file_name_ui,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@app.get("/posts", response_model=PostListData)
async def get_posts(session: SessionDep) -> PostListData:
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    rows = result.scalars().all()
    return PostListData(posts=rows)


@app.delete("/posts/{post_id}")
async def delete_post(session: SessionDep, post_id: uuid.UUID = Path()) -> dict[str, str | bool]:
    existing = await session.get(Post, post_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")

    await _delete_post_remote(existing)

    await session.delete(existing)
    await session.commit()
    return {"success": True, "message": "Post deleted successfully"}
