# app/tasks/parse_task.py
import logging
import re
from celery import Task
from app.celery_app import celery_app
from app.core.pdf_parser import extract_text_from_pdf
from db.session_sync import get_session
from db.crud_paper_sync import update_paper_status, get_paper_by_id
from db.models import PaperStatus

logger = logging.getLogger(__name__)

LLM_MAX_CHARS = 8000

def clean_pdf_text(text: str) -> str:
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def save_full_text(session, paper_id: str, full_text: str) -> None:
    paper = get_paper_by_id(session, paper_id)
    if paper:
        paper.full_text = full_text
        session.commit()

@celery_app.task(
    name="app.tasks.parse.parse_pdf",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def parse_pdf_task(self: Task, paper_id: str, pdf_path: str) -> dict:
    logger.info("[Parse Task] 开始解析 PDF paper_id=%s", paper_id)

    # 1. 标记为 PARSING
    try:
        with get_session() as session:
            update_paper_status(session, paper_id, PaperStatus.PARSING)
    except Exception as exc:
        logger.warning("更新 PARSING 状态失败（非致命）: %s", exc)

    # 2. 提取 PDF 文本
    try:
        raw_text = extract_text_from_pdf(pdf_path, max_chars=0)
        logger.info("[Parse Task] PDF 提取成功 paper_id=%s, raw_chars=%d", paper_id, len(raw_text))
    except Exception as exc:
        logger.exception("[Parse Task] PDF 提取失败 paper_id=%s", paper_id)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        else:
            with get_session() as session:
                update_paper_status(session, paper_id, PaperStatus.FAILED)
            raise

    # 3. 清洗 + 截断
    paper_text = clean_pdf_text(raw_text)
    if not paper_text.strip():
        logger.error("[Parse Task] PDF 文本为空 paper_id=%s", paper_id)
        with get_session() as session:
            update_paper_status(session, paper_id, PaperStatus.FAILED)
        raise ValueError("PDF extracted text is empty")

    # 4. 保存全文（用于搜索）
    try:
        with get_session() as session:
            save_full_text(session, paper_id, paper_text)
    except Exception as exc:
        logger.warning("保存全文失败（非致命）: %s", exc)

    # 5. 截断用于 LLM
    paper_text_for_llm = paper_text[:LLM_MAX_CHARS] if len(paper_text) > LLM_MAX_CHARS else paper_text

    # 6. 更新状态为 PENDING_EXTRACTION
    try:
        with get_session() as session:
            update_paper_status(session, paper_id, PaperStatus.PENDING_EXTRACTION)
    except Exception as exc:
        logger.warning("更新 PENDING_EXTRACTION 状态失败（非致命）: %s", exc)

    # 7. 触发 LLM 提取任务
    from app.tasks.llm_tasks import extract_key_points_task
    extract_key_points_task.delay(paper_id, paper_text_for_llm)

    logger.info("[Parse Task] 完成 paper_id=%s, chars=%d", paper_id, len(paper_text))
    return {"paper_id": paper_id, "chars": len(paper_text)}