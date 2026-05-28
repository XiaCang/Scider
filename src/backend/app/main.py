import os
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
from app.core.config import settings
from middleware.jwt_middleware import JWTAuthMiddleware
from module.user.controller.auth_router import router as auth_router
from module.user.controller.user_router import router as user_router
from module.user.controller.avatar_router import router as avatar_router
from module.user.controller.llm_provider_router import router as llm_provider_router

print("DATABASE_URL from env:", os.getenv("DATABASE_URL"))
app = FastAPI(
    title=settings.APP_NAME,
    description="Scider 学术论文管理系统 API 文档",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI 路径
    redoc_url="/redoc",  # ReDoc 路径
    openapi_url="/openapi.json",  # OpenAPI schema 路径
)

# ── JWT authentication middleware ──
app.add_middleware(JWTAuthMiddleware)

# ── CORS 跨域配置（最外层，确保所有响应都带上 CORS 头） ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 静态文件服务（用于PDF预览） ──
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
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(avatar_router)
app.include_router(llm_provider_router)
