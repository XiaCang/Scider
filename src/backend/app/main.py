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
from app.api.routes.graph_edit import router as graph_edit_router
from app.api.routes.notes import router as notes_router
from app.api.routes.chat_ws import router as chat_ws_router
from app.core.config import settings
from middleware.jwt_middleware import JWTAuthMiddleware
from module.user.controller.auth_router import router as auth_router
from module.user.controller.user_router import router as user_router
from module.user.controller.avatar_router import router as avatar_router
from module.user.controller.llm_provider_router import router as llm_provider_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Scider 学术论文管理系统 API 文档",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

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
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(avatar_router)
app.include_router(llm_provider_router)
