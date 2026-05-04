import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.tasks import router as tasks_router
from app.api.routes.papers import router as papers_router
from app.api.routes.folders import router as folders_router
from app.core.config import settings
from middleware.jwt_middleware import JWTAuthMiddleware
from module.user.controller.auth_router import router as auth_router
from module.user.controller.user_router import router as user_router

app = FastAPI(title=settings.APP_NAME)

# ── CORS 跨域配置 ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源,生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法(GET, POST, PUT, DELETE, OPTIONS等)
    allow_headers=["*"],  # 允许所有请求头
)

# ── JWT authentication middleware (ASGI middleware, not BaseHTTPMiddleware) ──
app.add_middleware(JWTAuthMiddleware)

# ── 静态文件服务（用于PDF预览） ──
UPLOAD_DIR_ABSOLUTE = str(Path(settings.UPLOAD_DIR).resolve())
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR_ABSOLUTE), name="uploads")


@app.on_event("startup")
async def startup():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(tasks_router, prefix=settings.API_PREFIX)
app.include_router(papers_router, prefix=settings.API_PREFIX)
app.include_router(folders_router, prefix=settings.API_PREFIX)
app.include_router(auth_router)
app.include_router(user_router)
