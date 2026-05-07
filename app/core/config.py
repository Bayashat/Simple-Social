from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and optional ``.env`` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str

    database_url: str = "sqlite+aiosqlite:///./test.db"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
