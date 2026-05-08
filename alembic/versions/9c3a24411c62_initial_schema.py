"""initial_schema

Revision ID: 9c3a24411c62
Revises:
Create Date: 2026-05-08 03:27:39.477359

"""

from collections.abc import Sequence

import sqlalchemy as sa
from fastapi_users_db_sqlalchemy.generics import GUID

from alembic import op

revision: str = "9c3a24411c62"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    poststorage = sa.Enum(
        "imagekit",
        "s3",
        name="poststorage",
        native_enum=False,
        length=16,
    )
    postfiletype = sa.Enum(
        "image",
        "video",
        "file",
        name="postfiletype",
        native_enum=False,
        length=16,
    )
    poststorage.create(bind, checkfirst=True)
    postfiletype.create(bind, checkfirst=True)

    op.create_table(
        "user",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_table(
        "posts",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("caption", sa.String(length=50), nullable=True),
        sa.Column(
            "storage",
            poststorage,
            nullable=False,
            server_default="imagekit",
        ),
        sa.Column("imagekit_file_id", sa.String(length=128), nullable=True),
        sa.Column("s3_bucket", sa.String(length=128), nullable=True),
        sa.Column("s3_object_key", sa.String(length=512), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("file_type", postfiletype, nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("posts")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
    poststorage = sa.Enum(
        "imagekit",
        "s3",
        name="poststorage",
        native_enum=False,
        length=16,
    )
    postfiletype = sa.Enum(
        "image",
        "video",
        "file",
        name="postfiletype",
        native_enum=False,
        length=16,
    )
    postfiletype.drop(op.get_bind(), checkfirst=True)
    poststorage.drop(op.get_bind(), checkfirst=True)
