"""
Celery task: compute embedding via OpenAI-compatible API and upsert into MySQL (paper_embedding.embedding JSON).
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy import select

from app.celery_app import celery_app
from app.core.config import settings
from app.core.embedding_client import create_embedding

logger = logging.getLogger(__name__)


def _ensure_backend_root_in_path() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    s = str(backend_root)
    if s not in sys.path:
        sys.path.insert(0, s)


async def _fetch_paper_embed_text(paper_id: str) -> str:
    """Load title/abstract/keypoints from Paper/KeyPoints for embedding."""
    _ensure_backend_root_in_path()
    from db.models import KeyPoints, Paper
    from db.session import get_session

    async with get_session() as session:
        result = await session.execute(select(Paper).where(Paper.id == paper_id))
        paper = result.scalar_one_or_none()
        if paper is None:
            return ""

        parts = [paper.title or "", paper.abstract or ""]
        kp_result = await session.execute(select(KeyPoints).where(KeyPoints.paper_id == paper_id))
        kp = kp_result.scalar_one_or_none()
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


async def _upsert_paper_embedding(paper_id: str, embedding: list[float]) -> None:
    from db.models import PaperEmbedding
    from db.session import get_session

    payload = [float(x) for x in embedding]

    async with get_session() as session:
        async with session.begin():
            row = await session.get(PaperEmbedding, paper_id)
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
        text = asyncio.run(_fetch_paper_embed_text(paper_id))

    if not text:
        logger.error("[Embed] no text for paper_id=%s", paper_id)
        raise ValueError(f"No text to embed for paper_id={paper_id}")

    try:
        vector = create_embedding(text)
    except Exception as exc:
        logger.exception("[Embed] API failed paper_id=%s", paper_id)
        raise self.retry(exc=exc)

    try:
        asyncio.run(_upsert_paper_embedding(paper_id, vector))
    except Exception as exc:
        logger.exception("[Embed] MySQL upsert failed paper_id=%s", paper_id)
        raise self.retry(exc=exc)

    logger.info("[Embed] done paper_id=%s dim=%s", paper_id, len(vector))
    return {
        "paper_id": paper_id,
        "model": settings.EMBEDDING_MODEL,
        "dim": len(vector),
    }
