"""
llm_tasks.py — Celery 任务：调用大模型提取论文四要素并写入数据库。

任务流程：
  1. 将 Paper.status 更新为 EXTRACTING
  2. 调用大模型，获取 JSON 格式四要素
  3. 解析 JSON 并截断至 200 字符
  4. 写入/更新 KeyPoints 表
  5. 将 Paper.status 更新为 PENDING_CONFIRMATION
  失败时将 Paper.status 更新为 FAILED 并记录错误
"""

import asyncio
import json
import logging
import re
import sys
from pathlib import Path

from app.celery_app import celery_app
from app.core.llm_client import chat_completion
from app.core.prompts import EXTRACT_SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


def _ensure_backend_root_in_path() -> None:
    """
    Ensure `src/backend` is in sys.path so `import db...` works
    under different worker launch locations/environments.
    """
    backend_root = Path(__file__).resolve().parents[2]
    backend_root_str = str(backend_root)
    if backend_root_str not in sys.path:
        sys.path.insert(0, backend_root_str)

# ─── JSON 解析 ────────────────────────────────────────────────────────────────

def _parse_json_response(raw: str) -> dict:
    """
    从模型原始回复中提取四要素 JSON。

    - 兼容模型将 JSON 包在 ```json … ``` 代码块内的情况。
    - 对每个字段截断至 200 字符，确保符合数据库约束。
    - 若缺少必须字段则抛出 ValueError。
    """
    text = raw.strip()

    # 去除可能存在的 Markdown 代码块标记
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()

    data = json.loads(text)

    required = {"background", "methodology", "innovation", "conclusion"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"LLM 返回 JSON 缺少字段: {missing}")

    # 截断至 200 字符，防止超出数据库字段限制
    for key in required:
        data[key] = str(data.get(key) or "").strip()[:200] or "暂无相关信息"

    return data


# ─── 异步数据库操作 ────────────────────────────────────────────────────────────

async def _set_paper_extracting(paper_id: str) -> None:
    """将 Paper.status 设为 EXTRACTING。"""
    from sqlalchemy import select
    _ensure_backend_root_in_path()
    from db.session import get_session
    from db.models import Paper, PaperStatus

    async with get_session() as session:
        async with session.begin():
            result = await session.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if paper:
                paper.status = PaperStatus.EXTRACTING


async def _persist_result(paper_id: str, key_points: dict) -> None:
    """将四要素写入 KeyPoints 表，并将 Paper.status 更新为 PENDING_CONFIRMATION。"""
    from sqlalchemy import select
    _ensure_backend_root_in_path()
    from db.session import get_session
    from db.models import Paper, KeyPoints, PaperStatus

    async with get_session() as session:
        async with session.begin():
            # 更新 Paper 状态
            p_result = await session.execute(select(Paper).where(Paper.id == paper_id))
            paper = p_result.scalar_one_or_none()
            if paper is None:
                logger.error("Paper %s 不存在，跳过写入", paper_id)
                return
            paper.status = PaperStatus.PENDING_CONFIRMATION

            # Upsert KeyPoints
            kp_result = await session.execute(
                select(KeyPoints).where(KeyPoints.paper_id == paper_id)
            )
            kp = kp_result.scalar_one_or_none()
            if kp is None:
                kp = KeyPoints(paper_id=paper_id)
                session.add(kp)

            kp.background = key_points["background"]
            kp.methodology = key_points["methodology"]
            kp.innovation = key_points["innovation"]
            kp.conclusion = key_points["conclusion"]
            kp.is_confirmed = False


async def _set_paper_failed(paper_id: str) -> None:
    """将 Paper.status 设为 FAILED。"""
    from sqlalchemy import select
    _ensure_backend_root_in_path()
    from db.session import get_session
    from db.models import Paper, PaperStatus

    async with get_session() as session:
        async with session.begin():
            result = await session.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if paper:
                paper.status = PaperStatus.FAILED


# ─── Celery Task ──────────────────────────────────────────────────────────────

@celery_app.task(
    name="app.tasks.llm.extract_key_points",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def extract_key_points_task(self, paper_id: str, paper_text: str) -> dict:
    """
    提取论文四要素的 Celery 任务。

    Args:
        paper_id:   Paper 表中的记录 ID。
        paper_text: 论文文本（摘要 + 正文，或纯摘要）。

    Returns:
        含四要素字段的字典（成功），或含 "error" 字段的字典（永久失败）。
    """
    logger.info("[LLM Task] 开始提取四要素 paper_id=%s", paper_id)

    # Step 1: 标记为提取中
    try:
        asyncio.run(_set_paper_extracting(paper_id))
    except Exception as exc:
        logger.warning("更新 EXTRACTING 状态失败（非致命）: %s", exc)

    # Step 2: 调用大模型
    try:
        user_prompt = build_user_prompt(paper_text)
        raw = chat_completion(EXTRACT_SYSTEM_PROMPT, user_prompt)
        logger.debug("[LLM Task] 原始回复 (前 300 字): %s", raw[:300])
    except Exception as exc:
        logger.exception("[LLM Task] 大模型调用失败 paper_id=%s", paper_id)
        try:
            asyncio.run(_set_paper_failed(paper_id))
        except Exception:
            pass
        raise self.retry(exc=exc)

    # Step 3: 解析 JSON
    try:
        key_points = _parse_json_response(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.exception("[LLM Task] JSON 解析失败 paper_id=%s", paper_id)
        try:
            asyncio.run(_set_paper_failed(paper_id))
        except Exception:
            pass
        raise self.retry(exc=exc)

    # Step 4: 写入数据库
    try:
        asyncio.run(_persist_result(paper_id, key_points))
    except Exception as exc:
        logger.exception("[LLM Task] 写入数据库失败 paper_id=%s", paper_id)
        try:
            asyncio.run(_set_paper_failed(paper_id))
        except Exception:
            pass
        raise self.retry(exc=exc)

    logger.info("[LLM Task] 完成 paper_id=%s", paper_id)
    return {
        "paper_id": paper_id,
        "background": key_points["background"],
        "methodology": key_points["methodology"],
        "innovation": key_points["innovation"],
        "conclusion": key_points["conclusion"],
    }
