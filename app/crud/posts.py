import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.models.posts import Post
from app.models.users import User


async def create_post(session: AsyncSession, post: Post) -> Post:
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


async def list_posts_for_feed(session: AsyncSession) -> list[Post]:
    result = await session.execute(
        select(Post)
        .join(User, Post.user_id == User.id)
        .options(contains_eager(Post.user))
        .order_by(Post.created_at.desc())
    )
    return list(result.unique().scalars().all())


async def get_post_by_id(session: AsyncSession, post_id: uuid.UUID) -> Post | None:
    return await session.get(Post, post_id)


async def delete_post(session: AsyncSession, post: Post) -> None:
    await session.delete(post)
    await session.commit()
