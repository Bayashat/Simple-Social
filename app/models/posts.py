import re
import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Self

from sqlalchemy import DateTime, Enum as SQLEnum, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, utc_now

RequiredStr = Annotated[str, mapped_column(String, nullable=False)]


class PostStorage(StrEnum):
    """Which object store holds the uploaded file."""

    IMAGEKIT = "imagekit"
    S3 = "s3"


class PostFileType(StrEnum):
    """Allowed persisted categories for uploaded media."""

    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"

    @classmethod
    def from_upload(cls, content_type: str | None, imagekit_file_type: str | None) -> Self:
        """Derive stored kind from MIME (primary) and ImageKit classification (fallback)."""
        mime = (content_type or "").split(";")[0].strip().lower()
        if mime.startswith("image/"):
            return cls.IMAGE
        if mime.startswith("video/"):
            return cls.VIDEO
        if (imagekit_file_type or "").lower() == "image":
            return cls.IMAGE
        return cls.FILE


def safe_upload_basename(filename: str) -> str:
    base = filename.strip() if filename.strip() else "upload"
    return re.sub(r"[^a-zA-Z0-9._-]", "_", base)[:180]


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    caption: Mapped[str | None] = mapped_column(String(50))
    storage: Mapped[PostStorage] = mapped_column(
        SQLEnum(PostStorage, native_enum=False, length=16),
        nullable=False,
        default=PostStorage.IMAGEKIT,
    )
    #: Set when `storage == imagekit`.
    imagekit_file_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    #: Set when `storage == s3`.
    s3_bucket: Mapped[str | None] = mapped_column(String(128), nullable=True)
    s3_object_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    url: Mapped[RequiredStr]
    file_type: Mapped[PostFileType] = mapped_column(
        SQLEnum(PostFileType, native_enum=False, length=16),
    )
    file_name: Mapped[RequiredStr]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
