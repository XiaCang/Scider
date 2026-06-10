from datetime import datetime

from app.celery_app import celery_app


@celery_app.task(name="app.tasks.ping")
def ping_task() -> dict:
    return {
        "message": "pong",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
