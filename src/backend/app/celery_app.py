# app/celery_app.py
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
    # 新增：每个 worker 一次只取一个任务，减少竞争
    worker_prefetch_multiplier=1,
)

# 线程池配置
celery_app.conf.update(
    worker_pool="threads",
    worker_concurrency=8,
)

celery_app.autodiscover_tasks(["app.tasks"])