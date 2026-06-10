import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.core.config import settings
from db.models import PaperNote, NoteImage, NoteSearch, Paper
from app.utils.sanitize import sanitize_html, html_to_text, extract_image_srcs


def _notes_base_dir() -> Path:
    # store notes under uploads/<...>/notes to be served by StaticFiles mounted at settings.UPLOAD_DIR
    base = Path(settings.UPLOAD_DIR)
    notes_dir = base / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    return notes_dir


async def save_upload_file(upload_file, note_id: Optional[str] = None) -> dict:
    """Save an UploadFile to disk. If note_id provided, save to final dir, else save to tmp dir.
    Returns dict with url, filename, size, mime_type
    """
    notes_dir = _notes_base_dir()
    if note_id:
        dest_dir = notes_dir / note_id
    else:
        dest_dir = notes_dir / "tmp"
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{Path(upload_file.filename).suffix}"
    dest_path = dest_dir / filename

    # read file content and write to disk
    content = await upload_file.read()
    await asyncio.to_thread(dest_path.write_bytes, content)

    size = dest_path.stat().st_size
    mime_type = getattr(upload_file, "content_type", None)

    # URL relative to /uploads mount: since settings.UPLOAD_DIR is mounted at /uploads,
    # and notes are saved under settings.UPLOAD_DIR/notes/..., the URL is /uploads/notes/...
    # Build posix path relative to upload dir's parent: we want '/uploads/notes/{...}'
    relative = Path("notes") / (note_id or "tmp") / filename
    url = f"/uploads/{relative.as_posix()}"

    return {"url": url, "filename": upload_file.filename, "mimeType": mime_type, "size": size, "path": str(dest_path)}


async def move_tmp_files_into_note(note_id: str, content_html: str) -> str:
    """Move any files referenced from tmp/ to note_id folder and replace URLs in content_html."""
    notes_dir = _notes_base_dir()
    tmp_dir = notes_dir / "tmp"
    note_dir = notes_dir / note_id
    note_dir.mkdir(parents=True, exist_ok=True)

    srcs = extract_image_srcs(content_html)
    for src in srcs:
        # expected src like /uploads/notes/tmp/<filename>
        if "/uploads/notes/tmp/" in src:
            filename = src.split("/uploads/notes/tmp/")[-1]
            src_path = tmp_dir / filename
            if src_path.exists():
                dest_path = note_dir / filename
                # move in thread
                await asyncio.to_thread(shutil.move, str(src_path), str(dest_path))
                new_rel = Path("notes") / note_id / filename
                new_url = f"/uploads/{new_rel.as_posix()}"
                content_html = content_html.replace(src, new_url)
    return content_html


async def create_note(session: AsyncSession, user_id: str, paper_id: str, title: Optional[str], content_html: Optional[str], content_format: str = "html") -> PaperNote:
    # sanitize
    safe_html = sanitize_html(content_html or "")
    content_text = html_to_text(safe_html)

    note = PaperNote(
        paper_id=paper_id,
        # legacy `content` column exists in DB schema and may be NOT NULL in migrations;
        # populate it with the plain-text extraction to ensure compatibility.
        content=content_text or "",
        title=title,
        content_html=safe_html,
        content_format=content_format,
        content_text=content_text,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)

    # move tmp files into note folder and update content_html
    updated_html = await move_tmp_files_into_note(note.id, note.content_html or "")
    if updated_html != (note.content_html or ""):
        note.content_html = updated_html
        note.content_text = html_to_text(updated_html)
        await session.commit()
        await session.refresh(note)

    # insert note_image entries if any
    img_srcs = extract_image_srcs(note.content_html or "")
    order = 0
    for src in img_srcs:
        img = NoteImage(note_id=note.id, url=src, filename=Path(src).name, order_index=order)
        session.add(img)
        order += 1
    await session.commit()

    # upsert note_search
    await upsert_note_search(session, note)

    return note


async def upsert_note_search(session: AsyncSession, note: PaperNote):
    # get paper title
    result = await session.execute(select(Paper).where(Paper.id == note.paper_id))
    paper = result.scalar_one_or_none()
    paper_title = paper.title if paper else None
    # include note title in content_text to expand search scope (title + body)
    combined_content = "".join([note.title or "", "\n", note.content_text or ""]).strip()

    sql = text(
        "INSERT INTO note_search (note_id, paper_id, note_title, paper_title, content_text, updated_at)"
        " VALUES (:note_id, :paper_id, :note_title, :paper_title, :content_text, NOW())"
        " ON DUPLICATE KEY UPDATE note_title=VALUES(note_title), paper_title=VALUES(paper_title), content_text=VALUES(content_text), updated_at=NOW()"
    )
    await session.execute(sql, {
        "note_id": note.id,
        "paper_id": note.paper_id,
        "note_title": note.title,
        "paper_title": paper_title,
        "content_text": combined_content,
    })
    await session.commit()


async def get_note(session: AsyncSession, note_id: str) -> Optional[PaperNote]:
    result = await session.execute(
        select(PaperNote).options(selectinload(PaperNote.images)).where(PaperNote.id == note_id)
    )
    note = result.scalar_one_or_none()
    return note


async def list_notes_by_paper(session: AsyncSession, paper_id: str, limit: int = 20, offset: int = 0) -> List[PaperNote]:
    result = await session.execute(
        select(PaperNote)
        .options(selectinload(PaperNote.images))
        .where(PaperNote.paper_id == paper_id)
        .order_by(PaperNote.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def update_note(session: AsyncSession, note_id: str, title: Optional[str], content_html: Optional[str], content_format: Optional[str]) -> Optional[PaperNote]:
    note = await get_note(session, note_id)
    if not note:
        return None
    changed = False
    if title is not None:
        note.title = title
        changed = True
    if content_html is not None:
        # Only update the stored HTML/text. Do NOT modify NoteImage rows here.
        # Changing image records during a PATCH can unintentionally remove images
        # when the client omits image tags. Keep image management separate
        # (handled by upload endpoint or explicit admin operations).
        safe_html = sanitize_html(content_html)
        note.content_html = safe_html
        note.content_text = html_to_text(safe_html)
        changed = True
    if content_format is not None:
        note.content_format = content_format
        changed = True
    if changed:
        await session.commit()
        await session.refresh(note)
        await upsert_note_search(session, note)
    return note


async def delete_note(session: AsyncSession, note_id: str) -> bool:
    note = await get_note(session, note_id)
    if not note:
        return False
    # delete images and files
    # remove DB entries
    from sqlalchemy import delete
    await session.execute(delete(NoteImage).where(NoteImage.note_id == note.id))
    await session.execute(delete(NoteSearch).where(NoteSearch.note_id == note.id))
    await session.delete(note)
    await session.commit()

    # remove file dir
    notes_dir = _notes_base_dir()
    note_dir = notes_dir / note_id
    if note_dir.exists():
        await asyncio.to_thread(shutil.rmtree, str(note_dir))
    return True


async def search_notes(session: AsyncSession, q: str, paper_id: Optional[str], limit: int = 20, offset: int = 0):
    # Use FULLTEXT MATCH to get scored results
    params = {"q": q}
    where = ""
    if paper_id:
        where = "AND ns.paper_id = :paper_id"
        params["paper_id"] = paper_id

    match_sql = text(
        "SELECT ns.note_id, ns.note_title, ns.paper_title, MATCH(ns.note_title, ns.paper_title, ns.content_text) AGAINST(:q IN NATURAL LANGUAGE MODE) AS score, ns.content_text, ns.updated_at"
        " FROM note_search ns JOIN paper_note pn ON pn.id = ns.note_id"
        " WHERE MATCH(ns.note_title, ns.paper_title, ns.content_text) AGAINST(:q IN NATURAL LANGUAGE MODE) " + where +
        " ORDER BY score DESC, ns.updated_at DESC"
    )
    res = await session.execute(match_sql, params)
    match_rows = res.fetchall()

    # transform match rows
    match_items = []
    match_ids = set()
    for row in match_rows:
        m = dict(row._mapping)
        # remove paper_title from response
        m.pop("paper_title", None)
        if "updated_at" in m and m["updated_at"] is not None:
            try:
                m["updated_at"] = m["updated_at"].isoformat()
            except Exception:
                m["updated_at"] = str(m["updated_at"])
        match_items.append(m)
        match_ids.add(m.get("note_id"))

    # Fallback LIKE search on paper_note to supplement results (covers cases where FULLTEXT excludes common/short words)
    like_items = []
    if paper_id:
        like_q = f"%{q}%"
        fallback_sql = text(
            "SELECT pn.id as note_id, pn.title as note_title, NULL as paper_title, pn.content_text, pn.updated_at, 0 as score"
            " FROM paper_note pn"
            " WHERE pn.paper_id = :paper_id AND (pn.title LIKE :like_q OR pn.content_text LIKE :like_q)"
            " ORDER BY pn.updated_at DESC"
        )
        f_res = await session.execute(fallback_sql, {"paper_id": paper_id, "like_q": like_q})
        f_rows = f_res.fetchall()
        for row in f_rows:
            m = dict(row._mapping)
            if m.get("note_id") in match_ids:
                continue
            # remove paper_title from fallback response as well
            m.pop("paper_title", None)
            if "updated_at" in m and m["updated_at"] is not None:
                try:
                    m["updated_at"] = m["updated_at"].isoformat()
                except Exception:
                    m["updated_at"] = str(m["updated_at"])
            like_items.append(m)

    # Merge: prefer match_items (by score), then like_items; compute total as union size
    all_items = match_items + like_items
    total_int = len(all_items)

    # apply offset/limit
    sliced = all_items[offset: offset + limit]
    return {"total": total_int, "items": sliced}
