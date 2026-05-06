import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated, Self

from sqlalchemy import DateTime, Enum as SQLEnum, String, Uuid
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATABASE_URL = "sqlite+aiosqlite:///./test.db"


def utc_now() -> datetime:
    """Insert default for ORM-created rows: timezone-aware UTC in the application."""
    return datetime.now(timezone.utc)


RequiredStr = Annotated[str, mapped_column(String, nullable=False)]


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


class Base(DeclarativeBase):
    """Declarative base for ORM models."""


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    caption: Mapped[str | None] = mapped_column(String(50))
    imagekit_file_id: Mapped[str] = mapped_column(String(128))
    url: Mapped[RequiredStr]
    file_type: Mapped[PostFileType] = mapped_column(
        SQLEnum(PostFileType, native_enum=False, length=16),
    )
    file_name: Mapped[RequiredStr]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now
    )


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_db_and_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
