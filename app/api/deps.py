import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import UserManager, auth_backend
from app.core.database import async_session_maker
from app.models.users import User


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(
    session: AsyncSession = Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, uuid.UUID]]:
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase[User, uuid.UUID] = Depends(get_user_db),
) -> AsyncGenerator[UserManager]:
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)

SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
UserDep = Annotated[User, Depends(current_active_user)]
