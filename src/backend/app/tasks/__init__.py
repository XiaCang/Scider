# app/tasks/__init__.py
from app.tasks import embedding_tasks, example_tasks, llm_tasks, parse_task, email_tasks

__all__ = ["embedding_tasks", "example_tasks", "llm_tasks", "parse_task", "email_tasks"]
