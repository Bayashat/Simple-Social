import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.posts import PostFileType, PostStorage


class PostCreate(BaseModel):
    title: str
    content: str


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    caption: str | None
    storage: PostStorage
    imagekit_file_id: str | None = None
    url: str
    file_type: PostFileType
    file_name: str
    created_at: datetime


class PostListData(BaseModel):
    posts: list[PostRead]
