from fastapi import FastAPI

from app.api.routes.tasks import router as tasks_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(tasks_router, prefix=settings.API_PREFIX)
