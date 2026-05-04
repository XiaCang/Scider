"""论文关键点 CRUD：保存四要素并标记为已确认。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud_paper import get_paper_by_id
from db.models import KeyPoints, Paper, PaperStatus


async def save_confirmed_key_points(
    session: AsyncSession,
    paper_id: str,
    user_id: str,
    *,
    background: str,
    method: str,
    innovation: str,
    conclusion: str,
) -> tuple[Paper | None, str | None]:
    """
    更新四要素，将 KeyPoints 标为已确认，Paper.status → CONFIRMED。
    返回 (paper, None) 成功；(None, 错误信息) 失败。
    """
    paper = await get_paper_by_id(session, paper_id)
    if paper is None or paper.user_id != user_id:
        return None, "论文不存在或无权访问"

    result = await session.execute(select(KeyPoints).where(KeyPoints.paper_id == paper_id))
    kp = result.scalar_one_or_none()

    if kp is None:
        kp = KeyPoints(paper_id=paper_id)
        session.add(kp)

    kp.background = background.strip()
    kp.methodology = method.strip()
    kp.innovation = innovation.strip()
    kp.conclusion = conclusion.strip()
    kp.is_confirmed = True
    kp.confirmed_at = datetime.now(timezone.utc)

    paper.status = PaperStatus.CONFIRMED

    await session.commit()
    await session.refresh(paper)
    await session.refresh(kp)
    return paper, None
