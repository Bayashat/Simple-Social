import uuid

from botocore.exceptions import ClientError
from fastapi import APIRouter, File, Form, HTTPException, Path, UploadFile
from imagekitio import APIConnectionError, APIStatusError, ImageKitError, omit
from sqlalchemy import select
from sqlalchemy.orm import contains_eager

from app.dependencies import SessionDep
from app.images import IMAGEKIT_UPLOAD_FOLDER, async_imagekit
from app.models.posts import Post, PostFileType, PostStorage
from app.models.users import User
from app.s3_storage import s3_bucket_name
from app.s3_storage import upload_bytes as s3_upload_bytes
from app.schemas import PostListData, PostRead, post_read_from_model
from app.services.post_media import delete_post_remote_files, upload_ui_filename
from app.users import UserDep

router = APIRouter(tags=["posts"])


@router.post("/upload", response_model=PostRead)
async def upload_file(
    session: SessionDep,
    user: UserDep,
    file: UploadFile = File(...),
    caption: str = Form(""),
    storage: PostStorage = Form(PostStorage.IMAGEKIT),
) -> PostRead:
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty file")

    trimmed_caption = caption.strip()
    file_name_ui = upload_ui_filename(file)

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
            user_id=user.id,
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
        return post_read_from_model(post, viewer_id=user.id, owner_email=user.email)

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
        user_id=user.id,
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
    return post_read_from_model(post, viewer_id=user.id, owner_email=user.email)


@router.get("/posts", response_model=PostListData)
async def get_posts(session: SessionDep, user: UserDep) -> PostListData:
    result = await session.execute(
        select(Post)
        .join(User, Post.user_id == User.id)
        .options(contains_eager(Post.user))
        .order_by(Post.created_at.desc())
    )
    rows = result.unique().scalars().all()
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


@router.delete("/posts/{post_id}")
async def delete_post(
    session: SessionDep, user: UserDep, post_id: uuid.UUID = Path()
) -> dict[str, str | bool]:
    existing = await session.get(Post, post_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    await delete_post_remote_files(existing)

    await session.delete(existing)
    await session.commit()
    return {"success": True, "message": "Post deleted successfully"}
