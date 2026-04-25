from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "scider",
    broker=settings.REDIS_BROKER_URL,
    backend=settings.REDIS_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
)

# Make sure worker auto-loads task modules.
celery_app.autodiscover_tasks(["app.tasks"])
