import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.imagekit import async_imagekit
from app.core.migrations import run_alembic_upgrade


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await asyncio.to_thread(run_alembic_upgrade)
    yield
    await async_imagekit.close()
