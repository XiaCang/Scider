import hashlib
import os

import aiofiles
from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from db.crud_paper import create_paper, get_paper_by_md5, get_papers_by_user
from db.crud_note import get_notes_by_paper, create_note, update_note
from db.session import get_db
from utils.response import success, error

router = APIRouter(prefix="/papers", tags=["papers"])

ALLOWED_EXTENSIONS = {".pdf"}


@router.get("/")
async def list_papers(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """获取当前用户的论文列表"""
    # ── 1. JWT 认证检查 ──
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # ── 2. 获取论文列表（预加载key_points） ──
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from db.models import Paper
    
    result = await session.execute(
        select(Paper)
        .where(Paper.user_id == user["id"])
        .options(selectinload(Paper.key_points))
        .order_by(Paper.created_at.desc())
        .limit(1000)
    )
    papers = result.scalars().all()
    
    # ── 3. 格式化返回数据 ──
    data = []
    for paper in papers:
        paper_data = {
            "id": paper.id,
            "title": paper.title,
            "authors": paper.authors or "",
            "year": paper.year or 0,
            "source": paper.source or "",
            "status": paper.status.value,
            "created_at": paper.created_at.isoformat() if paper.created_at else None,
        }
        
        # 添加四要素（如果存在）
        if paper.key_points:
            paper_data["keyPoints"] = {
                "background": paper.key_points.background or "",
                "method": paper.key_points.methodology or "",  # 前端使用method，后端使用methodology
                "innovation": paper.key_points.innovation or "",
                "conclusion": paper.key_points.conclusion or "",
            }
        else:
            paper_data["keyPoints"] = {
                "background": "",
                "method": "",
                "innovation": "",
                "conclusion": "",
            }
        
        data.append(paper_data)
    
    return success(data=data, msg="查询成功", code=0, status_code=200)


@router.get("/{paper_id}/pdf-info")
async def get_paper_pdf_info(
    paper_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """获取论文PDF预览信息"""
    # ── 1. JWT 认证检查 ──
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # ── 2. 查询论文 ──
    from sqlalchemy import select
    from db.models import Paper
    
    result = await session.execute(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == user["id"])
    )
    paper = result.scalar_one_or_none()
    
    if not paper:
        return error(msg="论文不存在或无权访问", code=404, data=None, status_code=404)
    
    if not paper.pdf_path:
        return error(msg="PDF文件路径不存在", code=404, data=None, status_code=404)
    
    # ── 3. 构建PDF访问URL ──
    # pdf_path 可能是相对路径（如 uploads/papers/xxx.pdf）或绝对路径
    # 需要转换为相对于 /uploads 挂载点的路径
    
    from pathlib import Path
    from app.core.config import settings
    
    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    pdf_path = Path(paper.pdf_path).resolve()
    
    # 计算相对于uploads目录的路径
    try:
        relative_path = pdf_path.relative_to(upload_dir)
        pdf_url = f"/uploads/{relative_path.as_posix()}"
    except ValueError:
        # 如果不在uploads目录下，使用文件名
        pdf_filename = pdf_path.name
        pdf_url = f"/uploads/{pdf_filename}"
    
    print(f"[DEBUG] PDF path: {paper.pdf_path}")
    print(f"[DEBUG] Upload dir: {upload_dir}")
    print(f"[DEBUG] Relative path: {relative_path if 'relative_path' in locals() else 'N/A'}")
    print(f"[DEBUG] PDF URL: {pdf_url}")
    
    # ── 4. 获取PDF页数（可选，前端可以自行获取） ──
    # 这里暂时返回0，前端vue-pdf-embed会自动获取页数
    page_count = 0
    
    return success(
        data={
            "paperId": paper.id,
            "title": paper.title,
            "pdfUrl": pdf_url,
            "pageCount": page_count,
        },
        msg="获取成功",
        code=0,
        status_code=200,
    )


@router.get("/{paper_id}/notes")
async def get_paper_notes(
    paper_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """获取论文的笔记列表"""
    # ── 1. JWT 认证检查 ──
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # ── 2. 验证用户是否有权访问该论文 ──
    from sqlalchemy import select
    from db.models import Paper
    
    result = await session.execute(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == user["id"])
    )
    paper = result.scalar_one_or_none()
    
    if not paper:
        return error(msg="论文不存在或无权访问", code=404, data=None, status_code=404)
    
    # ── 3. 获取笔记列表 ──
    notes = await get_notes_by_paper(session, paper_id)
    
    # ── 4. 格式化返回数据（转换为驼峰命名） ──
    data = [
        {
            "id": note.id,
            "paperId": note.paper_id,
            "content": note.content,
            "pageNumber": note.page_number,
            "selectedText": note.selected_text,
            "createdAt": note.created_at.isoformat() if note.created_at else None,
            "updatedAt": note.updated_at.isoformat() if note.updated_at else None,
        }
        for note in notes
    ]
    
    return success(data=data, msg="获取成功", code=0, status_code=200)


@router.post("/{paper_id}/notes")
async def create_paper_note(
    paper_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """创建论文笔记"""
    # ── 1. JWT 认证检查 ──
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # ── 2. 验证用户是否有权访问该论文 ──
    from sqlalchemy import select
    from db.models import Paper
    
    result = await session.execute(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == user["id"])
    )
    paper = result.scalar_one_or_none()
    
    if not paper:
        return error(msg="论文不存在或无权访问", code=404, data=None, status_code=404)
    
    # ── 3. 解析请求体 ──
    body = await request.json()
    content = body.get("content", "").strip()
    page_number = body.get("pageNumber")
    selected_text = body.get("selectedText")
    
    if not content:
        return error(msg="笔记内容不能为空", code=400, data=None, status_code=400)
    
    # ── 4. 创建笔记 ──
    note = await create_note(
        session=session,
        paper_id=paper_id,
        content=content,
        page_number=page_number,
        selected_text=selected_text,
    )
    
    # ── 5. 返回创建的笔记 ──
    data = {
        "id": note.id,
        "paperId": note.paper_id,
        "content": note.content,
        "pageNumber": note.page_number,
        "selectedText": note.selected_text,
        "createdAt": note.created_at.isoformat() if note.created_at else None,
        "updatedAt": note.updated_at.isoformat() if note.updated_at else None,
    }
    
    return success(data=data, msg="创建成功", code=0, status_code=200)


@router.patch("/{paper_id}/notes/{note_id}")
async def update_paper_note(
    paper_id: str,
    note_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """更新论文笔记"""
    # ── 1. JWT 认证检查 ──
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # ── 2. 验证用户是否有权访问该论文 ──
    from sqlalchemy import select
    from db.models import Paper, PaperNote
    
    result = await session.execute(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == user["id"])
    )
    paper = result.scalar_one_or_none()
    
    if not paper:
        return error(msg="论文不存在或无权访问", code=404, data=None, status_code=404)
    
    # ── 3. 验证笔记是否属于该论文 ──
    result = await session.execute(
        select(PaperNote).where(PaperNote.id == note_id, PaperNote.paper_id == paper_id)
    )
    note = result.scalar_one_or_none()
    
    if not note:
        return error(msg="笔记不存在", code=404, data=None, status_code=404)
    
    # ── 4. 解析请求体 ──
    body = await request.json()
    content = body.get("content")
    
    if content is not None and not content.strip():
        return error(msg="笔记内容不能为空", code=400, data=None, status_code=400)
    
    # ── 5. 更新笔记 ──
    updated_note = await update_note(
        session=session,
        note_id=note_id,
        content=content,
    )
    
    if not updated_note:
        return error(msg="更新失败", code=500, data=None, status_code=500)
    
    # ── 6. 返回更新后的笔记 ──
    data = {
        "id": updated_note.id,
        "paperId": updated_note.paper_id,
        "content": updated_note.content,
        "pageNumber": updated_note.page_number,
        "selectedText": updated_note.selected_text,
        "createdAt": updated_note.created_at.isoformat() if updated_note.created_at else None,
        "updatedAt": updated_note.updated_at.isoformat() if updated_note.updated_at else None,
    }
    
    return success(data=data, msg="更新成功", code=0, status_code=200)


@router.patch("/{paper_id}/key-points")
async def update_paper_key_points(
    paper_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """更新论文关键点（四要素）"""
    # ── 1. JWT 认证检查 ──
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # ── 2. 验证用户是否有权访问该论文 ──
    from sqlalchemy import select
    from db.models import Paper
    
    result = await session.execute(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == user["id"])
    )
    paper = result.scalar_one_or_none()
    
    if not paper:
        return error(msg="论文不存在或无权访问", code=404, data=None, status_code=404)
    
    # ── 3. 解析请求体 ──
    body = await request.json()
    key_points_data = body.get("keyPoints", {})
    
    background = key_points_data.get("background")
    methodology = key_points_data.get("method")  # 前端使用method，后端使用methodology
    innovation = key_points_data.get("innovation")
    conclusion = key_points_data.get("conclusion")
    
    # ── 4. 创建或更新关键点 ──
    from db.crud_paper import upsert_key_points
    from db.models import PaperStatus
    
    updated_key_points = await upsert_key_points(
        session=session,
        paper_id=paper_id,
        background=background,
        methodology=methodology,
        innovation=innovation,
        conclusion=conclusion,
    )
    
    # ── 5. 将论文状态更新为已确认 ──
    paper.status = PaperStatus.CONFIRMED
    await session.commit()
    
    # ── 6. 返回更新后的关键点数据 ──
    data = {
        "background": updated_key_points.background or "",
        "method": updated_key_points.methodology or "",  # 转换为前端字段名
        "innovation": updated_key_points.innovation or "",
        "conclusion": updated_key_points.conclusion or "",
    }
    
    return success(data=data, msg="保存成功", code=0, status_code=200)


@router.post("/upload")
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    # ── 1. JWT 认证检查 ──
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # ── 2. 文件类型校验 ──
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return error(msg="仅支持 PDF 文件", code=400, data=None, status_code=400)

    # ── 3. 读取文件内容并校验大小 ──
    content = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        return error(
            msg=f"文件大小不能超过 {settings.MAX_UPLOAD_SIZE_MB}MB",
            code=400,
            data=None,
            status_code=400,
        )

    # ── 4. MD5 去重 ──
    md5_hash = hashlib.md5(content).hexdigest()
    existing = await get_paper_by_md5(session, md5_hash)
    if existing:
        return error(msg="该论文已存在，请勿重复上传", code=409, data=None, status_code=409)

    # ── 5. 确保存储目录存在 ──
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # ── 6. 存储文件（以 MD5 命名） ──
    storage_filename = f"{md5_hash}.pdf"
    storage_path = os.path.join(settings.UPLOAD_DIR, storage_filename)
    async with aiofiles.open(storage_path, "wb") as f:
        await f.write(content)

    # ── 7. 写入数据库 ──
    title = file.filename.replace(".pdf", "") if file.filename else "untitled"
    paper = await create_paper(
        session=session,
        user_id=user["id"],
        title=title,
        pdf_path=storage_path,
        md5_hash=md5_hash,
        file_size=len(content),
    )

    # ── 8. 触发异步解析任务链 ──
    from app.tasks.parse_task import parse_pdf_task

    task = parse_pdf_task.delay(paper.id, storage_path)

    return success(
        data={
            "paper_id": paper.id,
            "filename": file.filename,
            "file_size": len(content),
            "md5": md5_hash,
            "status": paper.status.value,
            "task_id": task.id,
        },
        msg="上传成功，后台解析中",
        code=0,
        status_code=200,
    )


@router.delete("/{paper_id}")
async def delete_paper_endpoint(
    paper_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """删除论文（级联删除关联数据）"""
    # ── 1. JWT 认证检查 ──
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # ── 2. 删除论文 ──
    from db.crud_paper import delete_paper
    
    ok = await delete_paper(session=session, paper_id=paper_id, user_id=user["id"])
    
    if not ok:
        return error(msg="论文不存在或无权删除", code=404, data=None, status_code=404)

    return success(data=None, msg="删除成功", code=0, status_code=200)
