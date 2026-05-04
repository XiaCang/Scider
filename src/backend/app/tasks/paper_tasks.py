"""
paper_tasks.py — Celery 异步任务：PDF 解析与文本预处理

流程：
  1. 将论文状态置为 PARSING
  2. 用 PyMuPDF 提取 PDF 全文
  3. 清洗文本（去除断行、多余空白）
  4. 按标题分段
  5. 将状态更新为 PENDING_EXTRACTION（等待后续 LLM 提取）
  6. 任何异常均将状态置为 FAILED
"""

import asyncio
import logging
import re
from pathlib import Path

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 文本处理工具函数
# ---------------------------------------------------------------------------

def _extract_text(pdf_path: str) -> str:
    """用 PyMuPDF 逐页提取 PDF 文本，返回拼接后的全文字符串。"""
    import fitz  # PyMuPDF
    logger.debug("_extract_text opening pdf_path=%s", pdf_path)
    doc = fitz.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    logger.debug("_extract_text done pages=%d", len(pages))
    return "\n".join(pages)


def _clean(text: str) -> str:
    """
    清洗原始 PDF 文本：
    - 修复 PDF 断行导致的连字符拆词（e.g. "trans-\nformer" → "transformer"）
    - 合并连续空行（≥3 行 → 2 行）
    - 压缩行内多余空格/制表符
    """
    text = re.sub(r"-\n(\w)", r"\1", text)   # 连字符断行修复
    text = re.sub(r"\n{3,}", "\n\n", text)   # 多余空行合并
    text = re.sub(r"[ \t]+", " ", text)      # 行内空白压缩
    return text.strip()


def _segment(text: str) -> list[dict]:
    """
    按章节标题将文本分段，返回 [{"heading": ..., "content": ...}, ...] 列表。

    识别规则（正则）：
    - 数字编号标题：如 "1. Introduction"、"2.1 Method"
    - 全大写标题：如 "ABSTRACT"、"CONCLUSION"

    若未检测到任何标题，则将全文作为单一段落返回。
    """
    heading_re = re.compile(
        r"^(?:(?:\d+\.)+\s+[A-Z]|[A-Z][A-Z\s]{3,}$)", re.MULTILINE
    )
    positions = [m.start() for m in heading_re.finditer(text)]
    if not positions:
        logger.debug("_segment no headings found, returning full text as one section")
        return [{"heading": "FULL TEXT", "content": text}]

    sections = []
    for i, start in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        chunk = text[start:end].strip()
        first_line, _, body = chunk.partition("\n")
        sections.append({"heading": first_line.strip(), "content": body.strip()})

    logger.debug("_segment found %d sections", len(sections))
    return sections


# ---------------------------------------------------------------------------
# 任务链辅助
# ---------------------------------------------------------------------------

def _dispatch_llm_task(paper_id: str, paper_text: str) -> None:
    """解析完成后立即派发 LLM 提取任务，实现任务链。"""
    from app.tasks.llm_tasks import extract_key_points_task
    task = extract_key_points_task.delay(paper_id, paper_text)
    logger.info("_dispatch_llm_task queued llm_task_id=%s paper_id=%s", task.id, paper_id)


# ---------------------------------------------------------------------------
# Celery 任务
# ---------------------------------------------------------------------------

@celery_app.task(name="app.tasks.parse_paper", bind=True)
def parse_paper_task(self, paper_id: str) -> dict:
    """
    Celery 任务入口：解析指定论文的 PDF 文件。

    Args:
        paper_id: 数据库中 Paper 记录的主键。

    Returns:
        {"paper_id": ..., "status": "parsed"|"no_pdf", "sections": [...]}

    Side effects:
        - 任务开始时将 Paper.status 置为 PARSING
        - 成功后置为 PENDING_EXTRACTION
        - 失败时置为 FAILED
    """
    logger.info("[task:%s] parse_paper START paper_id=%s", self.request.id, paper_id)

    try:
        result = asyncio.run(_run(self.request.id, paper_id))
        logger.info(
            "[task:%s] parse_paper DONE paper_id=%s status=%s sections=%d",
            self.request.id, paper_id, result["status"], len(result.get("sections", [])),
        )
        return result
    except Exception as e:
        logger.error(
            "[task:%s] parse_paper FAILED paper_id=%s error=%s",
            self.request.id, paper_id, e, exc_info=True,
        )
        asyncio.run(_set_failed(paper_id))
        raise


async def _run(task_id: str, paper_id: str) -> dict:
    """异步执行体：数据库操作 + PDF 解析。"""
    from db.session import get_session
    from db.models import Paper, PaperStatus

    # 1. 标记为解析中
    async with get_session() as session:
        paper = await session.get(Paper, paper_id)
        if paper is None:
            raise ValueError(f"Paper not found: paper_id={paper_id}")
        paper.status = PaperStatus.PARSING
        await session.commit()
        logger.debug("[task:%s] status → PARSING paper_id=%s", task_id, paper_id)

    pdf_path = paper.pdf_path

    # 2. 无 PDF 文件时跳过解析，用摘要文本触发 LLM 提取
    if not pdf_path or not Path(pdf_path).exists():
        logger.warning(
            "[task:%s] no PDF found paper_id=%s pdf_path=%s, skipping parse",
            task_id, paper_id, pdf_path,
        )
        async with get_session() as session:
            p = await session.get(Paper, paper_id)
            p.status = PaperStatus.PENDING_EXTRACTION
            await session.commit()
        # 用摘要作为 LLM 输入（可能为空字符串，LLM 任务会处理）
        abstract_text = paper.abstract or ""
        _dispatch_llm_task(paper_id, abstract_text)
        return {"paper_id": paper_id, "status": "no_pdf", "sections": []}

    # 3. 提取 → 清洗 → 分段
    logger.info("[task:%s] extracting text pdf_path=%s", task_id, pdf_path)
    raw = _extract_text(pdf_path)
    cleaned = _clean(raw)
    sections = _segment(cleaned)
    logger.info("[task:%s] text ready chars=%d sections=%d", task_id, len(cleaned), len(sections))

    # 4. 更新状态为等待 LLM 提取
    async with get_session() as session:
        p = await session.get(Paper, paper_id)
        p.status = PaperStatus.PENDING_EXTRACTION
        await session.commit()
        logger.debug("[task:%s] status → PENDING_EXTRACTION paper_id=%s", task_id, paper_id)

    # 5. 链式触发 LLM 提取任务，拼接各段正文作为输入
    paper_text = "\n\n".join(
        f"{s['heading']}\n{s['content']}" for s in sections if s.get("content")
    )
    _dispatch_llm_task(paper_id, paper_text)

    return {"paper_id": paper_id, "status": "parsed", "sections": sections}


async def _set_failed(paper_id: str) -> None:
    """将论文状态置为 FAILED（仅在任务异常时调用）。"""
    from db.session import get_session
    from db.models import Paper, PaperStatus
    async with get_session() as session:
        p = await session.get(Paper, paper_id)
        if p:
            p.status = PaperStatus.FAILED
            await session.commit()
            logger.warning("_set_failed paper_id=%s status → FAILED", paper_id)
