import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL")


def _pool_settings():
    return {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
    }


def get_async_engine(echo: bool = False):
    url = os.getenv("DATABASE_URL") or DATABASE_URL
    if not url:
        raise RuntimeError("DATABASE_URL not set in environment")
    engine = create_async_engine(
        url,
        echo=echo,
        **_pool_settings(),
    )
    return engine


def get_session_factory(echo: bool = False):
    engine = get_async_engine(echo=echo)
    return sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_session(echo: bool = False):
    """Async context manager that yields an AsyncSession.

    Usage:
        async with get_session() as session:
            ...
    """
    factory = get_session_factory(echo=echo)
    async with factory() as session:
        yield session


async def create_tables_if_needed(echo: bool = False):
    """Helper to create tables from metadata in-code for quick testing.
    This runs `Base.metadata.create_all()` using an async engine.
    """
    from .base import Base

    engine = get_async_engine(echo=echo)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
