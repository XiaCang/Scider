from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from .models import User


async def create_user(session: AsyncSession, email: str, password_hash: str, name: Optional[str] = None) -> User:
    user = User(email=email, password=password_hash, name=name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    q = select(User).where(User.email == email)
    res = await session.execute(q)
    return res.scalars().first()


async def get_user(session: AsyncSession, user_id: str) -> Optional[User]:
    q = select(User).where(User.id == user_id)
    res = await session.execute(q)
    return res.scalars().first()


async def update_user_name(session: AsyncSession, user_id: str, new_name: str) -> Optional[User]:
    q = update(User).where(User.id == user_id).values(name=new_name).execution_options(synchronize_session="fetch")
    await session.execute(q)
    await session.commit()
    return await get_user(session, user_id)


async def delete_user(session: AsyncSession, user_id: str) -> bool:
    q = delete(User).where(User.id == user_id)
    res = await session.execute(q)
    await session.commit()
    return res.rowcount > 0
