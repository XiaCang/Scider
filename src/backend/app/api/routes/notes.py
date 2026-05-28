import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Request, UploadFile, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.utils.sanitize import sanitize_html
from app.api.schemas.notes import CreateNoteRequest, UpdateNoteRequest
from app.services.notes_service import (
    save_upload_file,
    create_note as svc_create_note,
    get_note as svc_get_note,
    list_notes_by_paper as svc_list_notes_by_paper,
    update_note as svc_update_note,
    delete_note as svc_delete_note,
    search_notes as svc_search_notes,
)
from db.session import get_db
from utils.response import success, error

router = APIRouter(prefix="/notes", tags=["notes"]) 


@router.post('/uploads')
async def upload_note_image(
    request: Request,
    file: UploadFile = File(...),
    paperId: Optional[str] = Query(None),
    noteId: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
):
    user = getattr(request.state, 'user', None)
    if not user:
        return error(msg='未认证', code=401, data=None, status_code=401)

    # basic mime/type check
    content_type = getattr(file, 'content_type', '') or ''
    if not content_type.startswith('image/'):
        return error(msg='仅支持图片上传', code=400, data=None, status_code=400)

    # save directly into note folder if noteId provided, else save to tmp
    info = await save_upload_file(file, note_id=noteId if noteId else None)
    # if noteId provided, save db record in note_image
    if noteId:
        from db.models import NoteImage

        img = NoteImage(note_id=noteId, url=info['url'], filename=info['filename'], mime_type=info.get('mimeType'), size=info.get('size'))
        session.add(img)
        await session.commit()
        await session.refresh(img)
        data = {
            "id": img.id,
            "noteId": img.note_id,
            "url": img.url,
            "filename": img.filename,
            "mimeType": img.mime_type,
            "size": img.size,
            "createdAt": img.created_at.isoformat() if img.created_at else None,
        }
        return success(data=data, msg='上传成功')

    data = {"url": info['url'], "filename": info['filename'], "mimeType": info['mimeType'], "size": info['size']}
    return success(data=data, msg='上传成功')


@router.post('/')
async def create_note(request: Request, body: CreateNoteRequest = Body(...), session: AsyncSession = Depends(get_db)):
    user = getattr(request.state, 'user', None)
    if not user:
        return error(msg='未认证', code=401, data=None, status_code=401)

    paper_id = body.paperId
    title = body.title
    content_html = body.contentHtml or ''
    content_format = body.contentFormat or 'html'

    if not paper_id:
        return error(msg='paperId 必填', code=400, data=None, status_code=400)

    # verify paper ownership
    from sqlalchemy import select
    from db.models import Paper
    res = await session.execute(select(Paper).where(Paper.id == paper_id, Paper.user_id == user['id']))
    paper = res.scalar_one_or_none()
    if not paper:
        return error(msg='论文不存在或无权访问', code=404, data=None, status_code=404)

    note = await svc_create_note(session, user['id'], paper_id, title, content_html, content_format)
    data = {
        'id': note.id,
        'paperId': note.paper_id,
        'title': note.title,
        'contentHtml': note.content_html,
        'contentFormat': note.content_format,
        'createdAt': note.created_at.isoformat() if note.created_at else None,
        'updatedAt': note.updated_at.isoformat() if note.updated_at else None,
    }
    return success(data=data, msg='创建成功')


@router.get('/')
async def list_notes(paperId: str = Query(...), page: int = 1, pageSize: int = 20, session: AsyncSession = Depends(get_db), request: Request = None):
    # JWT check
    user = None
    if request:
        user = getattr(request.state, 'user', None)
    if not user:
        return error(msg='未认证', code=401, data=None, status_code=401)

    offset = (page - 1) * pageSize
    notes = await svc_list_notes_by_paper(session, paperId, limit=pageSize, offset=offset)
    data = []
    for note in notes:
        first_image = None
        if note.images:
            first_image = note.images[0].url
        excerpt = (note.content_text or '')[:200]
        data.append({
            'id': note.id,
            'paperId': note.paper_id,
            'title': note.title,
            'excerpt': excerpt,
            'firstImageUrl': first_image,
            'updatedAt': note.updated_at.isoformat() if note.updated_at else None,
        })
    return success(data={'total': len(data), 'items': data}, msg='查询成功')



@router.get('/search')
async def search(q: str = Query(...), paperId: Optional[str] = None, page: int = 1, pageSize: int = 20, session: AsyncSession = Depends(get_db), request: Request = None):
    user = getattr(request.state, 'user', None)
    if not user:
        return error(msg='未认证', code=401, data=None, status_code=401)

    offset = (page - 1) * pageSize
    res = await svc_search_notes(session, q, paperId, limit=pageSize, offset=offset)
    return success(data=res, msg='搜索完成')


@router.get('/{note_id}/images')
async def get_note_images(note_id: str, session: AsyncSession = Depends(get_db), request: Request = None):
    user = getattr(request.state, 'user', None)
    if not user:
        return error(msg='未认证', code=401, data=None, status_code=401)

    from sqlalchemy import select
    from db.models import NoteImage

    res = await session.execute(select(NoteImage).where(NoteImage.note_id == note_id).order_by(NoteImage.order_index))
    imgs = res.scalars().all()
    items = []
    for img in imgs:
        items.append({
            'id': img.id,
            'url': img.url,
            'filename': img.filename,
            'orderIndex': img.order_index,
            'createdAt': img.created_at.isoformat() if img.created_at else None,
        })
    return success(data={'total': len(items), 'items': items}, msg='查询成功')


@router.get('/{note_id}')
async def get_note(note_id: str, session: AsyncSession = Depends(get_db), request: Request = None):
    user = getattr(request.state, 'user', None)
    if not user:
        return error(msg='未认证', code=401, data=None, status_code=401)

    note = await svc_get_note(session, note_id)
    if not note:
        return error(msg='笔记不存在', code=404, data=None, status_code=404)
    images = [{'id': img.id, 'url': img.url, 'orderIndex': img.order_index} for img in note.images]
    data = {
        'id': note.id,
        'paperId': note.paper_id,
        'title': note.title,
        'contentHtml': note.content_html,
        'contentFormat': note.content_format,
        'contentText': note.content_text,
        'images': images,
        'createdAt': note.created_at.isoformat() if note.created_at else None,
        'updatedAt': note.updated_at.isoformat() if note.updated_at else None,
    }
    return success(data=data, msg='查询成功')


@router.patch('/{note_id}')
async def patch_note(note_id: str, request: Request, body: UpdateNoteRequest = Body(...), session: AsyncSession = Depends(get_db)):
    user = getattr(request.state, 'user', None)
    if not user:
        return error(msg='未认证', code=401, data=None, status_code=401)

    title = body.title
    content_html = body.contentHtml
    content_format = body.contentFormat

    note = await svc_update_note(session, note_id, title, content_html, content_format)
    if not note:
        return error(msg='更新失败或笔记不存在', code=404, data=None, status_code=404)
    return success(data={'id': note.id}, msg='更新成功')


@router.delete('/{note_id}')
async def remove_note(note_id: str, session: AsyncSession = Depends(get_db), request: Request = None):
    user = getattr(request.state, 'user', None)
    if not user:
        return error(msg='未认证', code=401, data=None, status_code=401)

    ok = await svc_delete_note(session, note_id)
    if not ok:
        return error(msg='删除失败或笔记不存在', code=404, data=None, status_code=404)
    return success(data=None, msg='删除成功')

