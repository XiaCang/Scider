# db/session_sync.py
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set")

# 将异步驱动替换为同步驱动
sync_url = DATABASE_URL
if "mysql+aiomysql://" in sync_url:
    sync_url = sync_url.replace("mysql+aiomysql://", "mysql+pymysql://")
elif "mysql+asyncmy://" in sync_url:
    sync_url = sync_url.replace("mysql+asyncmy://", "mysql+pymysql://")
elif "postgresql+asyncpg://" in sync_url:
    sync_url = sync_url.replace("postgresql+asyncpg://", "postgresql://")

# 打印确认（启动 Celery 时会输出，帮助调试）
print(f"[session_sync] Original URL: {DATABASE_URL}")
print(f"[session_sync] Sync URL: {sync_url}")

SYNC_DATABASE_URL = sync_url

def _pool_settings():
    return {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
        "pool_pre_ping": True,
    }

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(SYNC_DATABASE_URL, **_pool_settings())
    return _engine

_SessionFactory = None

def get_session_factory():
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionFactory

@contextmanager
def get_session() -> Session:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()