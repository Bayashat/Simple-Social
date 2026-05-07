import uuid

from fastapi import APIRouter, File, Form, HTTPException, Path, UploadFile

from app.api.deps import SessionDep, UserDep
from app.models.posts import PostStorage
from app.schemas import PostListData, PostRead
from app.services import posts as post_service

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
    trimmed = caption.strip()
    file_name_ui = post_service.upload_ui_filename(file)
    return await post_service.upload_new_post(
        session,
        user,
        payload=payload,
        content_type=file.content_type,
        file_name_ui=file_name_ui,
        caption=trimmed,
        storage=storage,
    )


@router.get("/posts", response_model=PostListData)
async def get_posts(session: SessionDep, user: UserDep) -> PostListData:
    return await post_service.list_posts(session, user)


@router.delete("/posts/{post_id}")
async def delete_post(
    session: SessionDep,
    user: UserDep,
    post_id: uuid.UUID = Path(),
) -> dict[str, str | bool]:
    return await post_service.delete_owned_post(session, user, post_id)
