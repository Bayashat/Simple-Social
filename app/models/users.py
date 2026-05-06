import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Self

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, utc_now

RequiredStr = Annotated[str, mapped_column(String, nullable=False)]


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
