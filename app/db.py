import uuid
from typing import TYPE_CHECKING, cast

from sqlalchemy import insert, inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from sqlalchemy.schema import Table

DATABASE_URL = "sqlite+aiosqlite:///./test.db"


class Base(DeclarativeBase):
    """Declarative base for ORM models."""


engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def _canonical_uuid_text(value: object) -> str:
    if isinstance(value, uuid.UUID):
        return str(value)
    return str(uuid.UUID(str(value)))


def _migrate_sqlite_post_guid_columns(connection: Connection) -> None:
    """
    Older SQLite DDL used SQLAlchemy ``Uuid`` (CHAR(32) hex).
    FastAPI Users stores ``user.id`` as ``GUID`` (CHAR(36) with hyphens).
    Same logical UUID compares unequal as text — rebuild ``posts`` with aligned types.
    """
    if connection.dialect.name != "sqlite":
        return

    inspector = inspect(connection)
    if not inspector.has_table("posts"):
        return

    pragma_rows = connection.execute(text("PRAGMA table_info(posts)")).fetchall()
    user_row = next((r for r in pragma_rows if r[1] == "user_id"), None)
    if user_row is None:
        return
    col_type = (user_row[2] or "").upper().replace(" ", "")
    # Current model uses GUID / CHAR(36); legacy was CHAR(32) from ``Uuid``.
    if col_type != "CHAR(32)":
        return

    # Import models so ``Post.__table__`` reflects GUID columns matching ``user``.
    from app.models.posts import Post

    rows = [dict(row) for row in connection.execute(text("SELECT * FROM posts")).mappings()]

    connection.execute(text("PRAGMA foreign_keys=OFF"))
    connection.execute(text('DROP TABLE "posts"'))

    post_table = cast("Table", Post.__table__)
    post_table.create(bind=connection, checkfirst=True)

    for row in rows:
        connection.execute(
            insert(post_table).values(
                id=_canonical_uuid_text(row["id"]),
                user_id=_canonical_uuid_text(row["user_id"]),
                caption=row["caption"],
                storage=row["storage"],
                imagekit_file_id=row["imagekit_file_id"],
                s3_bucket=row["s3_bucket"],
                s3_object_key=row["s3_object_key"],
                url=row["url"],
                file_type=row["file_type"],
                file_name=row["file_name"],
                created_at=row["created_at"],
            )
        )

    connection.execute(text("PRAGMA foreign_keys=ON"))


async def create_db_and_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_sqlite_post_guid_columns)
