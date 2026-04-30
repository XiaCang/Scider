import os
from pathlib import Path

from fastapi import FastAPI

from app.api.routes.tasks import router as tasks_router
from app.api.routes.papers import router as papers_router
from app.core.config import settings
from middleware.jwt_middleware import JWTAuthMiddleware

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
