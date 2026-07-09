from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import BlogPost, User


async def find_user_by_email(session: AsyncSession, email: str):
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def find_user_by_id(session: AsyncSession, user_id: int):
    return await session.get(User, user_id)

async def add_user(session: AsyncSession, user):
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def find_post_by_title(session: AsyncSession, title: str):
    result = await session.execute(select(BlogPost).where(BlogPost.title == title))
    return result.scalar_one_or_none()

async def get_all_posts(session: AsyncSession, per_page: int, page: int):
    result = await session.execute(
        select(BlogPost)
        .options(selectinload(BlogPost.author))
        .order_by(BlogPost.date.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    )
    posts = result.scalars().all()

    result_total = await session.execute(select(func.count()).select_from(BlogPost))
    total = result_total.scalar_one()
    return posts, total

async def get_post_by_id(session: AsyncSession, post_id: int):
    result = await session.execute(
        select(BlogPost)
        .where(BlogPost.id == post_id)
        .options(selectinload(BlogPost.author))
    )
    return result.scalar_one_or_none()

async def add_post(session: AsyncSession, post: BlogPost):
    session.add(post)
    await session.commit()
    await session.refresh(post, ["author"])
    return post

async def delete_post(session: AsyncSession, post_id: int):
    post = await get_post_by_id(session, post_id)
    await session.delete(post)
    await session.commit()

async def patch_post(session: AsyncSession, post_id: int, fields):
    post = await get_post_by_id(session, post_id)
    for key, value in fields.items():
        setattr(post, key, value)
    await session.commit()
    await session.refresh(post, ["author"])
    return post
