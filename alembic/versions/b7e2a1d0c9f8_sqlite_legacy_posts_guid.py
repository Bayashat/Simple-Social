"""Legacy SQLite: posts.user_id stored as CHAR(32); align to GUID CHAR(36) like user.id.

Revision ID: b7e2a1d0c9f8
Revises: 9c3a24411c62
Create Date: 2026-05-08

"""

from collections.abc import Sequence
from typing import TYPE_CHECKING, cast

import sqlalchemy as sa
from sqlalchemy import insert, text

from alembic import op

if TYPE_CHECKING:
    from sqlalchemy.schema import Table


revision: str = "b7e2a1d0c9f8"
down_revision: str | Sequence[str] | None = "9c3a24411c62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _canonical_uuid_text(value: object) -> str:
    import uuid

    if isinstance(value, uuid.UUID):
        return str(value)
    return str(uuid.UUID(str(value)))


def upgrade() -> None:
    connection = op.get_bind()
    if connection.dialect.name != "sqlite":
        return

    inspector = sa.inspect(connection)
    if not inspector.has_table("posts"):
        return

    pragma_rows = connection.execute(text("PRAGMA table_info(posts)")).fetchall()
    user_row = next((r for r in pragma_rows if r[1] == "user_id"), None)
    if user_row is None:
        return
    col_type = (user_row[2] or "").upper().replace(" ", "")
    if col_type != "CHAR(32)":
        return

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


def downgrade() -> None:
    """No-op: UUID column widening cannot be safely reversed."""
