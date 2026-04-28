from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .models import Paper, PaperStatus


async def create_paper(
    session: AsyncSession,
    user_id: str,
    title: str,
    pdf_path: str,
    md5_hash: str,
    file_size: int,
    folder_id: Optional[str] = None,
) -> Paper:
    paper = Paper(
        user_id=user_id,
        title=title,
        pdf_path=pdf_path,
        md5_hash=md5_hash,
        file_size=file_size,
        folder_id=folder_id,
        status=PaperStatus.PENDING_PARSING,
    )
    session.add(paper)
    await session.commit()
    await session.refresh(paper)
    return paper


async def get_paper_by_md5(session: AsyncSession, md5_hash: str) -> Optional[Paper]:
    q = select(Paper).where(Paper.md5_hash == md5_hash)
    res = await session.execute(q)
    return res.scalars().first()


async def get_paper_by_id(session: AsyncSession, paper_id: str) -> Optional[Paper]:
    q = select(Paper).where(Paper.id == paper_id)
    res = await session.execute(q)
    return res.scalars().first()


async def get_papers_by_user(
    session: AsyncSession, user_id: str, skip: int = 0, limit: int = 20
) -> list[Paper]:
    q = (
        select(Paper)
        .where(Paper.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Paper.created_at.desc())
    )
    res = await session.execute(q)
    return list(res.scalars().all())


async def update_paper_status(
    session: AsyncSession, paper_id: str, status: PaperStatus
) -> Optional[Paper]:
    q = (
        update(Paper)
        .where(Paper.id == paper_id)
        .values(status=status)
        .execution_options(synchronize_session="fetch")
    )
    await session.execute(q)
    await session.commit()
    return await get_paper_by_id(session, paper_id)


async def update_paper_metadata(
    session: AsyncSession,
    paper_id: str,
    *,
    title: Optional[str] = None,
    authors: Optional[str] = None,
    abstract: Optional[str] = None,
    doi: Optional[str] = None,
    year: Optional[int] = None,
) -> Optional[Paper]:
    updates = {}
    if title is not None:
        updates["title"] = title
    if authors is not None:
        updates["authors"] = authors
    if abstract is not None:
        updates["abstract"] = abstract
    if doi is not None:
        updates["doi"] = doi
    if year is not None:
        updates["year"] = year

    if not updates:
        return await get_paper_by_id(session, paper_id)

    q = (
        update(Paper)
        .where(Paper.id == paper_id)
        .values(**updates)
        .execution_options(synchronize_session="fetch")
    )
    await session.execute(q)
    await session.commit()
    return await get_paper_by_id(session, paper_id)
