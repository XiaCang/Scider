"""
Celery task: compute embedding via OpenAI-compatible API and upsert into MySQL (paper_embedding.embedding JSON).
"""

import logging
from typing import Optional

from sqlalchemy import select

from app.celery_app import celery_app
from app.core.config import settings
from app.core.embedding_client import create_embedding
from db.session_sync import get_session
from db.models import Paper, KeyPoints, PaperEmbedding

logger = logging.getLogger(__name__)


def _fetch_paper_embed_text(paper_id: str) -> str:
    """Load title/abstract/keypoints from Paper/KeyPoints for embedding (synchronous)."""
    with get_session() as session:
        paper = session.get(Paper, paper_id)
        if paper is None:
            return ""

        parts = [paper.title or "", paper.abstract or ""]
        kp = session.execute(
            select(KeyPoints).where(KeyPoints.paper_id == paper_id)
        ).scalar_one_or_none()
        if kp:
            parts.extend(
                [
                    kp.background or "",
                    kp.methodology or "",
                    kp.innovation or "",
                    kp.conclusion or "",
                ]
            )
        return "\n".join(p for p in parts if p).strip()


def _upsert_paper_embedding(paper_id: str, embedding: list[float]) -> None:
    """Insert or update embedding record (synchronous)."""
    payload = [float(x) for x in embedding]

    with get_session() as session:
        row = session.get(PaperEmbedding, paper_id)
        if row is None:
            session.add(
                PaperEmbedding(
                    paper_id=paper_id,
                    embedding=payload,
                    model_name=settings.EMBEDDING_MODEL,
                )
            )
        else:
            row.embedding = payload
            row.model_name = settings.EMBEDDING_MODEL
        session.commit()


@celery_app.task(
    name="app.tasks.embed_paper",
    bind=True,
    max_retries=3,
    default_retry_delay=20,
)
def embed_paper_task(self, paper_id: str, embed_text: Optional[str] = None) -> dict:
    """
    Compute embedding for ``embed_text`` or load text from Paper/KeyPoints.

    Returns:
        ``paper_id``, ``model``, ``dim``.
    """
    logger.info("[Embed] start paper_id=%s", paper_id)

    text = (embed_text or "").strip()
    if not text:
        text = _fetch_paper_embed_text(paper_id)

    if not text:
        logger.error("[Embed] no text for paper_id=%s", paper_id)
        raise ValueError(f"No text to embed for paper_id={paper_id}")

    try:
        vector = create_embedding(text)
    except Exception as exc:
        logger.exception("[Embed] API failed paper_id=%s", paper_id)
        raise self.retry(exc=exc)

    try:
        _upsert_paper_embedding(paper_id, vector)
    except Exception as exc:
        logger.exception("[Embed] MySQL upsert failed paper_id=%s", paper_id)
        raise self.retry(exc=exc)

    logger.info("[Embed] done paper_id=%s dim=%s", paper_id, len(vector))
    return {
        "paper_id": paper_id,
        "model": settings.EMBEDDING_MODEL,
        "dim": len(vector),
    }