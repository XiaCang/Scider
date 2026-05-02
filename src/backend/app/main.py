from fastapi import FastAPI

from app.api.routes.tasks import router as tasks_router
from app.api.routes.discover import router as discover_router
from app.api.routes.papers import router as papers_router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


app.include_router(tasks_router, prefix=settings.API_PREFIX)
app.include_router(discover_router, prefix=settings.API_PREFIX)
app.include_router(papers_router, prefix=settings.API_PREFIX)
