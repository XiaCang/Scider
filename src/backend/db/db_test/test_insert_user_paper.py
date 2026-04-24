"""Quick integration test: create user + paper + keypoints and verify relations.

Run with:
  python -m src.test.test_insert_user_paper

This script is for local developer verification only.
"""
import asyncio
import os
import sys
from sqlalchemy import select, delete

# Prefer package-relative import when running as module; fallback inserts src into sys.path
try:
    from ..session import get_session, create_tables_if_needed
    from ..models import User, Paper, KeyPoints, PaperStatus
except Exception:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from backend.db.session import get_session, create_tables_if_needed
    from backend.db.models import User, Paper, KeyPoints, PaperStatus


async def ensure_clean(session):
    # remove test artifacts if present
    await session.execute(delete(KeyPoints).where(KeyPoints.id != None))
    await session.execute(delete(Paper).where(Paper.doi == "test-doi-1"))
    await session.execute(delete(User).where(User.email == "testuser@example.com"))
    await session.commit()


async def main():
    if not os.getenv("DATABASE_URL"):
        print("ERROR: set DATABASE_URL before running tests")
        return

    # create tables if needed
    await create_tables_if_needed(echo=False)

    async with get_session() as session:
        # cleanup previous runs
        await ensure_clean(session)

        # create user
        u = User(email="testuser@example.com", password="hash", name="Test User")
        session.add(u)
        await session.commit()
        await session.refresh(u)
        print("Created user:", u.id, u.email)

        # create paper linked to user
        p = Paper(
            title="Test Paper 1",
            authors='["T Author"]',
            abstract="This is a test.",
            doi="test-doi-1",
            user_id=u.id,
            pdf_path="/tmp/test.pdf",
            status=PaperStatus.PENDING_PARSING,
        )
        session.add(p)
        await session.commit()
        await session.refresh(p)
        print("Created paper:", p.id, p.title)

        # create keypoints
        kp = KeyPoints(paper_id=p.id, background="bg", methodology="m", innovation="i", conclusion="c")
        session.add(kp)
        await session.commit()
        await session.refresh(kp)
        print("Created keypoints:", kp.id)

        # verify relations
        res = await session.execute(select(Paper).where(Paper.id == p.id))
        paper_db = res.scalars().first()
        if paper_db is None:
            print("ERROR: paper not found")
            return
        print("Paper owner id:", paper_db.user_id)

        # fetch user via relation
        res = await session.execute(select(User).where(User.id == paper_db.user_id))
        owner = res.scalars().first()
        print("Owner email:", owner.email)

        

    print("Test completed")


if __name__ == "__main__":
    asyncio.run(main())
