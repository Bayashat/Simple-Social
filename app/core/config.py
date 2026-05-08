from functools import lru_cache
from typing import Self
from urllib.parse import quote_plus

from pydantic import AliasChoices, Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and optional ``.env`` file.

    Database connectivity uses **one of**:

    - ``DATABASE_URL``: full async URL (e.g. SQLite ``sqlite+aiosqlite:///...`` or Postgres
      ``postgresql+asyncpg://...``), or
    - ``POSTGRES_USER`` + ``POSTGRES_PASSWORD`` plus optional ``POSTGRES_HOST``,
      ``POSTGRES_PORT``, ``POSTGRES_DB`` (no credentials in repo; set these in ``.env``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str

    db_url_raw: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL"),
    )
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5433)
    postgres_db: str = Field(default="social_blog")

    jwt_lifetime_seconds: int = 3600

    imagekit_private_key: str | None = None
    imagekit_upload_folder: str = "/posts"
    imagekit_url_endpoint: str | None = None
    imagekit_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("IMAGEKIT_URL"),
    )

    aws_s3_bucket: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AWS_S3_BUCKET", "S3_BUCKET"),
    )
    aws_region: str = Field(
        default="us-east-1",
        validation_alias=AliasChoices("AWS_REGION", "AWS_DEFAULT_REGION"),
    )
    s3_key_prefix: str = "posts"
    aws_endpoint_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("AWS_ENDPOINT_URL", "S3_ENDPOINT_URL"),
    )
    s3_public_base_url: str | None = None
    s3_object_acl: str = ""

    @property
    def imagekit_public_url_base(self) -> str | None:
        return self.imagekit_url_endpoint or self.imagekit_url

    @model_validator(mode="after")
    def validate_database_config(self) -> Self:
        has_direct = self.db_url_raw is not None and self.db_url_raw.strip() != ""
        has_pg = (
            self.postgres_user is not None
            and self.postgres_password is not None
            and self.postgres_user.strip() != ""
            and self.postgres_password != ""
        )
        if not has_direct and not has_pg:
            msg = (
                "Database configuration missing: set DATABASE_URL, or set POSTGRES_USER and "
                "POSTGRES_PASSWORD (and optionally POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB)."
            )
            raise ValueError(msg)
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        if self.db_url_raw is not None and self.db_url_raw.strip() != "":
            url = self.db_url_raw.strip()
            if url.startswith("postgres://"):
                return url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url

        assert self.postgres_user is not None
        assert self.postgres_password is not None
        user_q = quote_plus(self.postgres_user)
        password_q = quote_plus(self.postgres_password)
        return (
            f"postgresql+asyncpg://{user_q}:{password_q}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
