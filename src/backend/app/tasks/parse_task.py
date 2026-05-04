"""
parse_task.py — Celery 任务：解析 PDF 后启动 LLM 四要素提取。

任务链: parse_pdf_task → extract_key_points_task

流程:
  1. 将 Paper.status 从 PENDING_PARSING 更新为 PARSING
  2. 调用 pdf_parser 提取纯文本
  3. 将 Paper.status 更新为 PENDING_EXTRACTION
  4. 触发 extract_key_points_task（chain 调用）
"""

import asyncio
import logging

from app.celery_app import celery_app
from app.core.pdf_parser import extract_text_from_pdf

logger = logging.getLogger(__name__)


# ─── 异步数据库操作 ────────────────────────────────────────────────────────────


async def _set_paper_parsing(paper_id: str) -> None:
    """将 Paper.status 设为 PARSING。"""
    from sqlalchemy import select
    from db.session import get_session
    from db.models import Paper, PaperStatus

    async with get_session() as session:
        async with session.begin():
            result = await session.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if paper:
                paper.status = PaperStatus.PARSING


async def _set_paper_pending_extraction(paper_id: str) -> None:
    """将 Paper.status 设为 PENDING_EXTRACTION。"""
    from sqlalchemy import select
    from db.session import get_session
    from db.models import Paper, PaperStatus

    async with get_session() as session:
        async with session.begin():
            result = await session.execute(select(Paper).where(Paper.id == paper_id))
            paper = result.scalar_one_or_none()
            if paper:
                paper.status = PaperStatus.PENDING_EXTRACTION


async def _set_paper_failed(paper_id: str) -> None:
    """将 Paper.status 设为 FAILED。"""
    from sqlalchemy import select
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
    name="app.tasks.parse.parse_pdf",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def parse_pdf_task(self, paper_id: str, pdf_path: str) -> dict:
    """
    PDF 解析任务：提取文本后 chain 到 LLM 四要素提取。

    Args:
        paper_id: Paper 表中的记录 ID。
        pdf_path: PDF 文件的存储路径。

    Returns:
        含 paper_id 和文本长度的字典（成功）。
    """
    logger.info("[Parse Task] 开始解析 PDF paper_id=%s", paper_id)

    # Step 1: 标记为解析中
    try:
        asyncio.run(_set_paper_parsing(paper_id))
        logger.info("[Parse Task] 状态更新为 PARSING paper_id=%s", paper_id)
    except Exception as exc:
        logger.warning("更新 PARSING 状态失败（非致命）: %s", exc)

    # Step 2: 提取 PDF 文本
    try:
        paper_text = extract_text_from_pdf(pdf_path, max_chars=0)
        logger.info("[Parse Task] PDF 提取成功 paper_id=%s, chars=%d", paper_id, len(paper_text))
    except Exception as exc:
        logger.exception("[Parse Task] PDF 提取失败 paper_id=%s", paper_id)
        try:
            asyncio.run(_set_paper_failed(paper_id))
        except Exception:
            pass
        raise self.retry(exc=exc)

    if not paper_text.strip():
        logger.error("[Parse Task] PDF 文本为空 paper_id=%s", paper_id)
        try:
            asyncio.run(_set_paper_failed(paper_id))
        except Exception:
            pass
        raise self.retry(exc=ValueError("PDF extracted text is empty"))

    # Step 3: 更新状态为 PENDING_EXTRACTION
    try:
        asyncio.run(_set_paper_pending_extraction(paper_id))
    except Exception as exc:
        logger.warning("更新 PENDING_EXTRACTION 状态失败（非致命）: %s", exc)

    # Step 4: 派发 LLM 提取任务
    from app.tasks.llm_tasks import extract_key_points_task

    extract_key_points_task.delay(paper_id, paper_text)

    logger.info(
        "[Parse Task] 解析完成并触发 LLM 提取 paper_id=%s, chars=%d",
        paper_id,
        len(paper_text),
    )

    return {
        "paper_id": paper_id,
        "chars": len(paper_text),
    }
