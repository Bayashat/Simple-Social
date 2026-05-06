import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, Path, UploadFile
from imagekitio import APIConnectionError, APIStatusError, ImageKitError, NotFoundError, omit
from sqlalchemy import select

from app.db import Post, PostFileType, create_db_and_tables
from app.dependencies import SessionDep
from app.images import IMAGEKIT_UPLOAD_FOLDER, async_imagekit
from app.schemas import PostListData, PostRead


def _upload_filename(upload: UploadFile) -> str:
    name = (upload.filename or "upload").strip()
    return name if name else "upload"


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
) -> PostRead:
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty file")

    trimmed_caption = caption.strip()
    description = trimmed_caption if trimmed_caption else omit

    try:
        ik = await async_imagekit.files.upload(
            file=payload,
            file_name=_upload_filename(file),
            folder=IMAGEKIT_UPLOAD_FOLDER,
            use_unique_file_name=True,
            description=description,
        )
    except APIStatusError as exc:
        if 400 <= exc.status_code < 500:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
        raise HTTPException(
            status_code=502,
            detail="ImageKit upload failed",
        ) from exc
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
        imagekit_file_id=ik.file_id,
        url=ik.url,
        file_type=PostFileType.from_upload(file.content_type, ik.file_type),
        file_name=ik.name or _upload_filename(file),
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@app.get("/posts", response_model=PostListData)
async def get_posts(session: SessionDep):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    rows = result.scalars().all()
    return PostListData(posts=rows)


@app.delete("/posts/{post_id}")
async def delete_post(session: SessionDep, post_id: uuid.UUID = Path()) -> dict[str, str | bool]:
    # result = await session.execute(select(Post).where(Post.id == post_id))
    # existing = result.scalar_one_or_none()

    existing = await session.get(Post, post_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")

    await _imagekit_delete_file(existing.imagekit_file_id)

    await session.delete(existing)
    await session.commit()
    return {"success": True, "message": "Post deleted successfully"}
