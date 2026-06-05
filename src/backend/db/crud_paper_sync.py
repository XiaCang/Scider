# db/crud_paper_sync.py
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from .models import Paper, PaperStatus


def create_paper(
    session: Session,
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
    session.commit()
    session.refresh(paper)
    return paper


def get_paper_by_md5(session: Session, md5_hash: str) -> Optional[Paper]:
    q = select(Paper).where(Paper.md5_hash == md5_hash)
    return session.execute(q).scalar_one_or_none()


def get_paper_by_id(session: Session, paper_id: str) -> Optional[Paper]:
    q = select(Paper).where(Paper.id == paper_id)
    return session.execute(q).scalar_one_or_none()


def get_papers_by_user(
    session: Session, user_id: str, skip: int = 0, limit: int = 20
) -> list[Paper]:
    q = (
        select(Paper)
        .where(Paper.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(Paper.created_at.desc())
    )
    return list(session.execute(q).scalars().all())


def update_paper_status(
    session: Session, paper_id: str, status: PaperStatus
) -> Optional[Paper]:
    paper = get_paper_by_id(session, paper_id)
    if paper:
        paper.status = status
        session.commit()
        session.refresh(paper)
    return paper


def update_paper_metadata(
    session: Session,
    paper_id: str,
    *,
    title: Optional[str] = None,
    authors: Optional[str] = None,
    abstract: Optional[str] = None,
    doi: Optional[str] = None,
    year: Optional[int] = None,
) -> Optional[Paper]:
    paper = get_paper_by_id(session, paper_id)
    if not paper:
        return None
    if title is not None:
        paper.title = title
    if authors is not None:
        paper.authors = authors
    if abstract is not None:
        paper.abstract = abstract
    if doi is not None:
        paper.doi = doi
    if year is not None:
        paper.year = year
    session.commit()
    session.refresh(paper)
    return paper


def upsert_key_points(
    session: Session,
    paper_id: str,
    background: Optional[str] = None,
    methodology: Optional[str] = None,
    innovation: Optional[str] = None,
    conclusion: Optional[str] = None,
):
    from .models import KeyPoints

    result = session.execute(
        select(KeyPoints).where(KeyPoints.paper_id == paper_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        if background is not None:
            existing.background = background
        if methodology is not None:
            existing.methodology = methodology
        if innovation is not None:
            existing.innovation = innovation
        if conclusion is not None:
            existing.conclusion = conclusion
        session.commit()
        session.refresh(existing)
        return existing
    else:
        key_points = KeyPoints(
            paper_id=paper_id,
            background=background,
            methodology=methodology,
            innovation=innovation,
            conclusion=conclusion,
        )
        session.add(key_points)
        session.commit()
        session.refresh(key_points)
        return key_points


def delete_paper(session: Session, paper_id: str, user_id: str) -> bool:
    from sqlalchemy import delete
    from .models import KeyPoints, PaperNote, PaperEmbedding

    paper = get_paper_by_id(session, paper_id)
    if not paper or paper.user_id != user_id:
        return False

    session.execute(delete(KeyPoints).where(KeyPoints.paper_id == paper_id))
    session.execute(delete(PaperNote).where(PaperNote.paper_id == paper_id))
    session.execute(delete(PaperEmbedding).where(PaperEmbedding.paper_id == paper_id))
    session.delete(paper)
    session.commit()
    return True