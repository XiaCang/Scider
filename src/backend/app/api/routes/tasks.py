from celery.result import AsyncResult
from fastapi import APIRouter

from app.celery_app import celery_app
from app.tasks.example_tasks import ping_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/ping")
def submit_ping_task() -> dict:
    task = ping_task.delay()
    return {"task_id": task.id, "status": task.status}


@router.get("/{task_id}")
def get_task_result(task_id: str) -> dict:
    result = AsyncResult(task_id, app=celery_app)
    payload = {
        "task_id": task_id,
        "status": result.status,
    }

    if result.successful():
        payload["result"] = result.result
    elif result.failed():
        payload["error"] = str(result.result)

    return payload
