import os
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.tasks import router as tasks_router
from app.api.routes.discover import router as discover_router
from app.api.routes.papers import router as papers_router
from app.api.routes.folders import router as folders_router
from app.api.routes.graph import router as graph_router
from app.api.routes.graph_edit import router as graph_edit_router
from app.api.routes.notes import router as notes_router
from app.api.routes.chat_ws import router as chat_ws_router
from app.api.routes.migration_router import router as migration_router
from app.core.config import settings
from middleware.jwt_middleware import JWTAuthMiddleware
from module.user.controller.auth_router import router as auth_router
from module.user.controller.user_router import router as user_router
from module.user.controller.avatar_router import router as avatar_router
from module.user.controller.llm_provider_router import router as llm_provider_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Scider 学术论文管理系统 API 文档",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.on_event("startup")
async def run_db_migrations():
    """
    应用启动时自动执行数据库迁移，确保 schema 与代码一致。
    可通过环境变量 SKIP_MIGRATIONS=true 跳过。
    """
    if os.getenv("SKIP_MIGRATIONS", "").lower() in ("true", "1", "yes"):
        logger.info("SKIP_MIGRATIONS=true，跳过数据库迁移")
        return

    logger.info("正在执行数据库迁移（alembic upgrade head）...")
    try:
        # 使用 SQLAlchemy create_all 同步表结构，避免 env.py 中 asyncio.run() 与已有事件循环冲突
        from db.session import get_async_engine
        from db.models import Base

        engine = get_async_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
        logger.info("数据库迁移完成（通过 create_all 同步 schema）")
    except Exception as e:
        logger.warning("数据库迁移失败（应用仍可启动，但 schema 可能不匹配）: %s", e)

app.add_middleware(JWTAuthMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR_ABSOLUTE = str(Path(settings.UPLOAD_DIR).resolve())
os.makedirs(UPLOAD_DIR_ABSOLUTE, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR_ABSOLUTE), name="uploads")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(tasks_router, prefix=settings.API_PREFIX)
app.include_router(discover_router, prefix=settings.API_PREFIX)
app.include_router(papers_router, prefix=settings.API_PREFIX)
app.include_router(folders_router, prefix=settings.API_PREFIX)
app.include_router(graph_router, prefix=settings.API_PREFIX)
app.include_router(graph_edit_router, prefix=settings.API_PREFIX)
app.include_router(notes_router, prefix=settings.API_PREFIX)
app.include_router(chat_ws_router, prefix=settings.API_PREFIX)
app.include_router(migration_router, prefix=settings.API_PREFIX)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(avatar_router)
app.include_router(llm_provider_router)
