from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import PaperNote


async def get_notes_by_paper(session: AsyncSession, paper_id: str) -> list[PaperNote]:
    """获取指定论文的所有笔记"""
    result = await session.execute(
        select(PaperNote)
        .where(PaperNote.paper_id == paper_id)
        .order_by(PaperNote.created_at.desc())
    )
    return list(result.scalars().all())


async def create_note(
    session: AsyncSession,
    paper_id: str,
    content: str,
    page_number: int | None = None,
    selected_text: str | None = None,
) -> PaperNote:
    """创建新笔记"""
    note = PaperNote(
        paper_id=paper_id,
        content=content,
        page_number=page_number,
        selected_text=selected_text,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note


async def update_note(
    session: AsyncSession,
    note_id: str,
    content: str | None = None,
    page_number: int | None = None,
    selected_text: str | None = None,
) -> PaperNote | None:
    """更新笔记"""
    result = await session.execute(
        select(PaperNote).where(PaperNote.id == note_id)
    )
    note = result.scalar_one_or_none()
    
    if not note:
        return None
    
    if content is not None:
        note.content = content
    if page_number is not None:
        note.page_number = page_number
    if selected_text is not None:
        note.selected_text = selected_text
    
    await session.commit()
    await session.refresh(note)
    return note


async def delete_note(session: AsyncSession, note_id: str) -> bool:
    """删除笔记"""
    result = await session.execute(
        select(PaperNote).where(PaperNote.id == note_id)
    )
    note = result.scalar_one_or_none()
    
    if not note:
        return False
    
    await session.delete(note)
    await session.commit()
    return True
