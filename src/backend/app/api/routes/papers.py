import hashlib
import os

import aiofiles
from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from db.crud_paper import create_paper, get_paper_by_md5, get_papers_by_user
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
