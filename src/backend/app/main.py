import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

from app.api.routes.tasks import router as tasks_router
from app.api.routes.papers import router as papers_router
from app.core.config import settings
from middleware.jwt_middleware import JWTAuthMiddleware
from module.user.controller.auth_router import router as auth_router
from module.user.controller.user_router import router as user_router

app = FastAPI(title=settings.APP_NAME)

# ── JWT authentication middleware (ASGI middleware, not BaseHTTPMiddleware) ──
app.add_middleware(JWTAuthMiddleware)


@app.on_event("startup")
async def startup():
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(tasks_router, prefix=settings.API_PREFIX)
app.include_router(papers_router, prefix=settings.API_PREFIX)
app.include_router(auth_router)
app.include_router(user_router)
