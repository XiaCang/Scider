# db/crud_keypoints_sync.py
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import KeyPoints, Paper, PaperStatus
from .crud_paper_sync import get_paper_by_id


def save_confirmed_key_points(
    session: Session,
    paper_id: str,
    user_id: str,
    *,
    background: str,
    methodology: str,
    innovation: str,
    conclusion: str,
):
    paper = get_paper_by_id(session, paper_id)
    if paper is None or paper.user_id != user_id:
        return None, "论文不存在或无权访问"

    kp = session.execute(
        select(KeyPoints).where(KeyPoints.paper_id == paper_id)
    ).scalar_one_or_none()

    if kp is None:
        kp = KeyPoints(paper_id=paper_id)
        session.add(kp)

    kp.background = background.strip()
    kp.methodology = methodology.strip()
    kp.innovation = innovation.strip()
    kp.conclusion = conclusion.strip()
    kp.is_confirmed = True
    kp.confirmed_at = datetime.now(timezone.utc)

    paper.status = PaperStatus.CONFIRMED

    session.commit()
    session.refresh(paper)
    session.refresh(kp)
    return paper, None