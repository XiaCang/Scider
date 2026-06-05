# app/tasks/llm_tasks.py
import json
import logging
import re
from celery import Task
from app.celery_app import celery_app
from app.core.llm_client import chat_completion
from app.core.prompts import EXTRACT_SYSTEM_PROMPT, build_user_prompt
from db.session_sync import get_session
from db.crud_paper_sync import get_paper_by_id, update_paper_status
from db.crud_keypoints_sync import save_confirmed_key_points
from db.models import PaperStatus

logger = logging.getLogger(__name__)

def _parse_json_response(raw: str) -> dict:
    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()
    data = json.loads(text)

    required_kp = {"background", "methodology", "innovation", "conclusion"}
    missing_kp = required_kp - set(data.keys())
    if missing_kp:
        raise ValueError(f"LLM 返回 JSON 缺少四要素字段: {missing_kp}")

    for key in required_kp:
        data[key] = str(data.get(key) or "").strip()[:200] or "暂无相关信息"

    if "title" in data:
        data["title"] = str(data["title"]).strip()[:1000] or None
    if "authors" in data:
        data["authors"] = str(data["authors"]).strip()[:500] or None
    if "year" in data:
        try:
            data["year"] = int(data["year"]) if data["year"] else None
        except (ValueError, TypeError):
            data["year"] = None
    if "source" in data:
        data["source"] = str(data["source"]).strip()[:500] or None
    return data

@celery_app.task(
    name="app.tasks.llm.extract_key_points",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def extract_key_points_task(self: Task, paper_id: str, paper_text: str) -> dict:
    logger.info("[LLM Task] 开始提取四要素 paper_id=%s", paper_id)

    # 标记为 EXTRACTING
    try:
        with get_session() as session:
            update_paper_status(session, paper_id, PaperStatus.EXTRACTING)
    except Exception as exc:
        logger.warning("更新 EXTRACTING 状态失败（非致命）: %s", exc)

    # 调用大模型
    try:
        user_prompt = build_user_prompt(paper_text)
        raw = chat_completion(EXTRACT_SYSTEM_PROMPT, user_prompt)
        logger.debug("[LLM Task] 原始回复 (前300字): %s", raw[:300])
    except Exception as exc:
        logger.exception("[LLM Task] 大模型调用失败 paper_id=%s", paper_id)
        if self.request.retries >= self.max_retries:
            with get_session() as session:
                update_paper_status(session, paper_id, PaperStatus.FAILED)
        raise self.retry(exc=exc)

    # 解析 JSON
    try:
        key_points = _parse_json_response(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.exception("[LLM Task] JSON 解析失败 paper_id=%s", paper_id)
        if self.request.retries >= self.max_retries:
            with get_session() as session:
                update_paper_status(session, paper_id, PaperStatus.FAILED)
        raise self.retry(exc=exc)

    # 写入数据库（使用同步 CRUD）
    try:
        with get_session() as session:
            # 先更新元数据和四要素（保存未确认状态）
            paper = get_paper_by_id(session, paper_id)
            if paper:
                if key_points.get("title"):
                    paper.title = key_points["title"]
                if key_points.get("authors"):
                    paper.authors = key_points["authors"]
                if key_points.get("year") is not None:
                    paper.year = key_points["year"]
                if key_points.get("source"):
                    paper.source = key_points["source"]
                paper.status = PaperStatus.PENDING_CONFIRMATION
                # 使用 upsert_key_points 或直接操作
                from db.crud_paper_sync import upsert_key_points
                upsert_key_points(
                    session, paper_id,
                    background=key_points["background"],
                    methodology=key_points["methodology"],
                    innovation=key_points["innovation"],
                    conclusion=key_points["conclusion"]
                )
                session.commit()
    except Exception as exc:
        logger.exception("[LLM Task] 写入数据库失败 paper_id=%s", paper_id)
        if self.request.retries >= self.max_retries:
            with get_session() as session:
                update_paper_status(session, paper_id, PaperStatus.FAILED)
        raise self.retry(exc=exc)

    # 触发向量化任务
    try:
        from app.tasks.embedding_tasks import embed_paper_task
        embed_paper_task.delay(paper_id)
        logger.info("[LLM Task] 已投递向量化任务 paper_id=%s", paper_id)
    except Exception as exc:
        logger.warning("[LLM Task] 投递向量化任务失败（非致命）: %s", exc)

    logger.info("[LLM Task] 完成 paper_id=%s", paper_id)
    return {
        "paper_id": paper_id,
        "background": key_points["background"],
        "methodology": key_points["methodology"],
        "innovation": key_points["innovation"],
        "conclusion": key_points["conclusion"],
    }