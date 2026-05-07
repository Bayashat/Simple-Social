import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.posts import Post, PostFileType, PostStorage


class PostCreate(BaseModel):
    title: str
    content: str


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    user_id: uuid.UUID
    caption: str | None
    storage: PostStorage
    imagekit_file_id: str | None = None
    s3_bucket: str | None = None
    s3_object_key: str | None = None
    url: str
    file_type: PostFileType
    file_name: str
    created_at: datetime
    is_owner: bool
    email: str


class PostListData(BaseModel):
    posts: list[PostRead]


def post_read_from_model(post: Post, *, viewer_id: uuid.UUID, owner_email: str) -> PostRead:
    """Map a persisted Post row to the public read schema."""
    return PostRead(
        id=post.id,
        user_id=post.user_id,
        is_owner=post.user_id == viewer_id,
        email=owner_email,
        caption=post.caption,
        storage=post.storage,
        imagekit_file_id=post.imagekit_file_id,
        s3_bucket=post.s3_bucket,
        s3_object_key=post.s3_object_key,
        url=post.url,
        file_type=post.file_type,
        file_name=post.file_name,
        created_at=post.created_at,
    )
