import os
import re
from datetime import datetime, timedelta
from typing import Optional, Dict

import jwt
from passlib.context import CryptContext
from sqlalchemy import select

from db.session import get_session
from db.models import User


pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def _validate_email(email: str) -> bool:
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None


def _hash_password(password: str) -> str:
    return pwd_ctx.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def _create_jwt(payload: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = payload.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


async def register_user(email: str, password: str, name: Optional[str] = None) -> Dict[str, str]:
    if not _validate_email(email):
        raise ValueError("invalid email")
    if not password or len(password) < 6:
        raise ValueError("password too short")

    hashed = _hash_password(password)

    async with get_session() as session:
        q = select(User).where(User.email == email)
        res = await session.execute(q)
        existing = res.scalars().first()
        if existing:
            raise ValueError("email already registered")

        user = User(email=email, password=hashed, name=name)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return {"id": user.id, "email": user.email, "name": user.name}


async def authenticate_user(email: str, password: str):
    async with get_session() as session:
        q = select(User).where(User.email == email)
        res = await session.execute(q)
        user = res.scalars().first()
        if not user:
            raise ValueError("invalid credentials")
        if not _verify_password(password, user.password):
            raise ValueError("invalid credentials")

        token = _create_jwt({"sub": user.id, "email": user.email})
        user_dict = {"id": user.id, "email": user.email, "name": user.name}
        return token, user_dict


async def get_user_by_id(user_id: str) -> Optional[Dict[str, str]]:
    async with get_session() as session:
        q = select(User).where(User.id == user_id)
        res = await session.execute(q)
        user = res.scalars().first()
        if not user:
            return None
        return {"id": user.id, "email": user.email, "name": user.name}


async def update_user_name(user_id: str, name: str) -> Optional[Dict[str, str]]:
    async with get_session() as session:
        q = select(User).where(User.id == user_id)
        res = await session.execute(q)
        user = res.scalars().first()
        if not user:
            return None
        user.name = name
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {"id": user.id, "email": user.email, "name": user.name}


async def change_user_password(email: str, new_password: str) -> Optional[Dict[str, str]]:
    """Change password for a user identified by email. Returns updated user dict or None if not found."""
    if not new_password or len(new_password) < 6:
        raise ValueError("password too short")

    hashed = _hash_password(new_password)
    async with get_session() as session:
        q = select(User).where(User.email == email)
        res = await session.execute(q)
        user = res.scalars().first()
        if not user:
            return None
        user.password = hashed
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {"id": user.id, "email": user.email, "name": user.name}
