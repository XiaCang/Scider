import sys

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

# Windows：prefork/billiard 多进程池易触发 fast_trace_task 等异常；默认 solo 单进程池。
# Linux/macOS 仍可用命令行覆盖：celery ... -P prefork -c 4
if sys.platform == "win32":
    celery_app.conf.update(
        worker_pool="solo",
        worker_concurrency=1,
    )

# Make sure worker auto-loads task modules.
celery_app.autodiscover_tasks(["app.tasks"])
