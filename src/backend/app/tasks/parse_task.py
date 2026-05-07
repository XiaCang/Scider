"""
parse_task.py — Celery 任务：解析 PDF 后启动 LLM 四要素提取。

任务链: parse_pdf_task → extract_key_points_task

流程:
  1. 将 Paper.status 从 PENDING_PARSING 更新为 PARSING
  2. 调用 pdf_parser 提取纯文本
  3. 清洗文本（修复断行、合并空行、压缩空白）
  4. 截断至 LLM_MAX_CHARS（默认 8000 字符，防 token 超限）
  5. 将 Paper.status 更新为 PENDING_EXTRACTION
  6. 触发 extract_key_points_task（chain 调用）
"""

import asyncio
import logging
import re

from app.celery_app import celery_app
from app.core.pdf_parser import extract_text_from_pdf

logger = logging.getLogger(__name__)

# ─── LLM 输入上限 ────────────────────────────────────────────────────────────────
LLM_MAX_CHARS = 8000


# ─── 文本清洗 ────────────────────────────────────────────────────────────────────


def clean_pdf_text(text: str) -> str:
    """清洗 PDF 提取文本：修复断行连字、合并多余空行、压缩空白。"""
    text = re.sub(r"-\n(\w)", r"\1", text)   # 连字符断行修复 (trans-\nformer → transformer)
    text = re.sub(r"\n{3,}", "\n\n", text)   # 连续空行合并
    text = re.sub(r"[ \t]+", " ", text)      # 行内多余空白压缩
    return text.strip()


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

    # Step 2: 提取 PDF 文本（不限制原始提取长度，后续清洗截断）
    try:
        raw_text = extract_text_from_pdf(pdf_path, max_chars=0)
        logger.info("[Parse Task] PDF 提取成功 paper_id=%s, raw_chars=%d", paper_id, len(raw_text))
    except Exception as exc:
        logger.exception("[Parse Task] PDF 提取失败 paper_id=%s", paper_id)
        try:
            asyncio.run(_set_paper_failed(paper_id))
        except Exception:
            pass
        raise self.retry(exc=exc)

    # Step 3: 清洗 + 截断
    paper_text = clean_pdf_text(raw_text)

    if not paper_text.strip():
        logger.error("[Parse Task] PDF 文本为空 paper_id=%s", paper_id)
        try:
            asyncio.run(_set_paper_failed(paper_id))
        except Exception:
            pass
        raise self.retry(exc=ValueError("PDF extracted text is empty"))

    # 截断至 LLM 输入上限（取开头最有价值的部分）
    if len(paper_text) > LLM_MAX_CHARS:
        logger.info(
            "[Parse Task] 文本超出上限 %d chars，截断至 %d chars paper_id=%s",
            len(paper_text), LLM_MAX_CHARS, paper_id,
        )
        paper_text = paper_text[:LLM_MAX_CHARS]

    logger.info("[Parse Task] 清洗后文本 paper_id=%s, chars=%d", paper_id, len(paper_text))

    # Step 4: 更新状态为 PENDING_EXTRACTION
    try:
        asyncio.run(_set_paper_pending_extraction(paper_id))
    except Exception as exc:
        logger.warning("更新 PENDING_EXTRACTION 状态失败（非致命）: %s", exc)

    # Step 5: 派发 LLM 提取任务
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
