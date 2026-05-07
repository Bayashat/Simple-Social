from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import create_db_and_tables
from app.core.imagekit import async_imagekit


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await create_db_and_tables()
    yield
    await async_imagekit.close()
