import asyncio
import hashlib
import logging
import os
from typing import List

import aiofiles
from fastapi import APIRouter, Depends, File, Request, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from db.crud_paper import create_paper, get_paper_by_md5, get_papers_by_user
from db.crud_note import get_notes_by_paper, create_note, update_note
from db.crud_keypoints import save_confirmed_key_points
from db.session import get_db
from utils.response import success, error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["papers"])


class KeyPointsIn(BaseModel):
    """前端和 LLM 统一使用 methodology。接收 method（兼容旧前端）。"""
    model_config = ConfigDict(populate_by_name=True)
    background: str = ""
    methodology: str = Field(default="", alias="method")
    innovation: str = ""
    conclusion: str = ""


class PatchKeyPointsBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    key_points: KeyPointsIn = Field(alias="keyPoints")

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


@router.get("/{paper_id}")
async def get_paper_detail(
    paper_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """获取单个论文详情"""
    # ── 1. JWT 认证检查 ──
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # ── 2. 查询论文（预加载key_points） ──
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from db.models import Paper
    
    result = await session.execute(
        select(Paper)
        .where(Paper.id == paper_id, Paper.user_id == user["id"])
        .options(selectinload(Paper.key_points))
    )
    paper = result.scalar_one_or_none()
    
    if not paper:
        return error(msg="论文不存在或无权访问", code=404, data=None, status_code=404)
    
    # ── 3. 格式化返回数据 ──
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
            "method": paper.key_points.methodology or "",
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
    
    return success(data=paper_data, msg="查询成功", code=0, status_code=200)


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
    raw_pdf_path = paper.pdf_path
    
    # 如果是相对路径，基于当前工作目录转为绝对路径
    if not os.path.isabs(raw_pdf_path):
        raw_pdf_path = os.path.join(os.getcwd(), raw_pdf_path)
    
    pdf_path = Path(raw_pdf_path).resolve()
    
    # 计算相对于uploads目录的路径
    try:
        relative_path = pdf_path.relative_to(upload_dir)
        pdf_url = f"/uploads/{relative_path.as_posix()}"
    except ValueError:
        # 如果不在uploads目录下，使用文件名
        pdf_filename = pdf_path.name
        pdf_url = f"/uploads/{pdf_filename}"
    
    # 同时检查PDF文件是否存在
    if not pdf_path.exists():
        logger.warning("pdf-info: PDF文件不存在 path=%s", pdf_path)
        # 不立即报错，前端仍可尝试通过 /pdf-file 接口获取
    
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


@router.post("/upload")
async def upload_pdf(
    request: Request,
    files: List[UploadFile] = File(..., description="最多5个PDF文件"),
    session: AsyncSession = Depends(get_db),
):
    """
    批量上传PDF文件，一次最多5个。
    返回每个文件的上传结果，包含 paper_id, task_id 等。
    """
    # ── 1. JWT 认证检查 ──
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # ── 2. 数量限制 ──
    if len(files) > 5:
        return error(msg="一次最多上传5个PDF文件", code=400, data=None, status_code=400)

    results = []          # 存储每个文件的上传结果
    tasks = []            # 存储异步任务对象（暂未使用）

    for file in files:
        # 单个文件处理逻辑（复用原有逻辑）
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            results.append({
                "filename": file.filename,
                "success": False,
                "msg": "仅支持 PDF 文件"
            })
            continue

        content = await file.read()
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_size:
            results.append({
                "filename": file.filename,
                "success": False,
                "msg": f"文件大小不能超过 {settings.MAX_UPLOAD_SIZE_MB}MB"
            })
            continue

        md5_hash = hashlib.md5(content).hexdigest()
        existing = await get_paper_by_md5(session, md5_hash)
        if existing:
            results.append({
                "filename": file.filename,
                "success": False,
                "msg": "该论文已存在，请勿重复上传",
                "paper_id": existing.id   # 可选，告知已存在的论文ID
            })
            continue

        # 存储文件
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        storage_filename = f"{md5_hash}.pdf"
        storage_path = os.path.join(settings.UPLOAD_DIR, storage_filename)
        async with aiofiles.open(storage_path, "wb") as f:
            await f.write(content)

        title = file.filename.replace(".pdf", "") if file.filename else "untitled"
        paper = await create_paper(
            session=session,
            user_id=str(user["id"]),
            title=title,
            pdf_path=storage_path,
            md5_hash=md5_hash,
            file_size=len(content),
        )

        # 触发异步解析任务
        from app.tasks.parse_task import parse_pdf_task
        task = parse_pdf_task.delay(paper.id, storage_path)

        results.append({
            "filename": file.filename,
            "success": True,
            "paper_id": paper.id,
            "task_id": task.id,
            "file_size": len(content),
            "md5": md5_hash,
            "status": paper.status.value,
        })

    return success(
        data={
            "total": len(files),
            "success_count": sum(1 for r in results if r["success"]),
            "results": results
        },
        msg=f"已处理{len(files)}个文件，成功{sum(1 for r in results if r['success'])}个",
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
    
@router.patch("/{paper_id}/key-points")
async def patch_key_points(
    paper_id: str,
    request: Request,
    body: PatchKeyPointsBody,
    session: AsyncSession = Depends(get_db),
):
    """
    保存四要素并视为「确认」：更新 KeyPoints、Paper.status=CONFIRMED，
    并异步投递向量化任务 ``embed_paper``。
    """
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)
    kp = body.key_points
    if not (
        kp.background.strip()
        and kp.methodology.strip()
        and kp.innovation.strip()
        and kp.conclusion.strip()
    ):
        return error(msg="四要素均需填写非空内容", code=400, data=None, status_code=200)

    paper, err = await save_confirmed_key_points(
        session,
        paper_id,
        user["id"],
        background=kp.background,
        methodology=kp.methodology,
        innovation=kp.innovation,
        conclusion=kp.conclusion,
    )
    if err:
        return error(msg=err, code=400, data=None, status_code=200)
    if paper is None:
        return error(msg="更新失败", code=500, data=None, status_code=200)

    from app.tasks.embedding_tasks import embed_paper_task

    embed_task = embed_paper_task.delay(paper_id)

    return success(
        data={
            "paper_id": paper.id,
            "status": paper.status.value,
            "embed_task_id": embed_task.id,
        },
        msg="已确认并提交向量化任务",
        code=0,
        status_code=200,
    )


@router.get("/{paper_id}/pdf-file")
async def get_pdf_file(
    paper_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """获取PDF文件流，设置 Content-Disposition: inline 防止浏览器下载。"""
    from fastapi.responses import FileResponse
    from sqlalchemy import select
    from db.models import Paper

    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    result = await session.execute(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == user["id"])
    )
    paper = result.scalar_one_or_none()

    if not paper or not paper.pdf_path:
        return error(msg="论文不存在或无PDF文件", code=404, data=None, status_code=404)

    pdf_path = paper.pdf_path
    if not os.path.exists(pdf_path):
        logger.warning("PDF文件不存在: %s (paper_id=%s)", pdf_path, paper_id)
        return error(msg="PDF文件不存在或已被删除", code=404, data=None, status_code=404)

    # 确保 pdf_path 是绝对路径（兼容相对路径存储的情况）
    if not os.path.isabs(pdf_path):
        pdf_path = os.path.join(os.getcwd(), pdf_path)

    if not os.path.exists(pdf_path):
        logger.warning("PDF文件不存在(尝试绝对路径后): %s", pdf_path)
        return error(msg="PDF文件不存在或已被删除", code=404, data=None, status_code=404)

    filename = f"{paper.title}.pdf" if paper.title else "paper.pdf"
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",  # 使用正确的 PDF MIME 类型
        filename=filename,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# ─── PDF 全文搜索接口 ──────────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    """搜索请求模型"""
    keyword: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
    page_number: int = Field(None, ge=1, description="限定页码（可选）")
    limit: int = Field(50, ge=1, le=200, description="返回结果数量上限")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


@router.post("/{paper_id}/search")
async def search_in_paper(
    paper_id: str,
    request: Request,
    body: SearchRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    在指定论文中搜索关键词（基于 MySQL FULLTEXT + ngram）
    
    - 支持中文/英文混合搜索
    - 返回匹配片段和高亮标记
    - 可限定特定页码搜索
    """
    import re
    
    # 1. JWT 认证
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)
    
    # 2. 验证论文归属
    from sqlalchemy import select
    from db.models import Paper
    
    result = await session.execute(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == user["id"])
    )
    paper = result.scalar_one_or_none()
    if not paper:
        return error(msg="论文不存在或无权访问", code=404, data=None, status_code=404)
    
    # 3. 检查是否有全文数据
    if not paper.full_text:
        return error(msg="论文尚未完成解析，请稍后再试", code=400, data=None, status_code=200)
    
    keyword = body.keyword.strip()
    if not keyword:
        return error(msg="搜索关键词不能为空", code=400, data=None, status_code=200)
    
    # 4. 执行 FULLTEXT 搜索
    try:
        from sqlalchemy import text
        
        # 使用 NATURAL LANGUAGE MODE 进行自然语言搜索
        query = text("""
            SELECT 
                MATCH(full_text) AGAINST (:keyword IN NATURAL LANGUAGE MODE) AS score
            FROM paper
            WHERE id = :paper_id
              AND MATCH(full_text) AGAINST (:keyword IN NATURAL LANGUAGE MODE)
            LIMIT 1
        """)
        
        search_result = await session.execute(
            query,
            {"paper_id": paper_id, "keyword": keyword}
        )
        row = search_result.fetchone()
        
        if not row or row.score == 0:
            return success(
                data={
                    "keyword": keyword,
                    "total_results": 0,
                    "results": []
                },
                msg="未找到匹配结果",
                code=0,
                status_code=200
            )
        
        # 5. 提取匹配片段并高亮
        full_text = paper.full_text
        
        # 查找所有匹配的上下文片段
        highlighted_results = _extract_highlights(full_text, keyword, body.limit)
        
        return success(
            data={
                "keyword": keyword,
                "total_results": len(highlighted_results),
                "results": highlighted_results
            },
            msg="搜索成功",
            code=0,
            status_code=200
        )
    
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        return error(msg="搜索服务异常", code=500, data=None, status_code=200)


def _extract_highlights(full_text: str, keyword: str, limit: int = 50) -> list:
    """
    从全文中提取关键词的上下文片段并高亮
    
    Args:
        full_text: 完整文本
        keyword: 搜索关键词
        limit: 最大返回片段数
    
    Returns:
        高亮片段列表
    """
    import re
    
    results = []
    context_length = 150  # 每个片段前后各取 150 字符作为上下文
    
    # 转义特殊字符，构建不区分大小写的正则
    escaped_keyword = re.escape(keyword)
    pattern = re.compile(escaped_keyword, re.IGNORECASE | re.UNICODE)
    
    # 查找所有匹配位置
    matches = list(pattern.finditer(full_text))
    
    for match in matches[:limit]:
        start_pos = max(0, match.start() - context_length)
        end_pos = min(len(full_text), match.end() + context_length)
        
        # 提取上下文
        context = full_text[start_pos:end_pos]
        
        # 在上下文中高亮关键词
        highlighted = pattern.sub(
            r'<em class="search-highlight">\g<0></em>', 
            context
        )
        
        # 如果截断了开头或结尾，添加省略号
        prefix = "..." if start_pos > 0 else ""
        suffix = "..." if end_pos < len(full_text) else ""
        
        # 估算页码（简单按每页 3000 字符估算）
        estimated_page = (match.start() // 3000) + 1
        
        results.append({
            "page_number": estimated_page,
            "content": context,
            "score": 1.0,  # MySQL FULLTEXT 不提供精确分数，统一设为 1.0
            "highlights": [f"{prefix}{highlighted}{suffix}"]
        })
    
    return results


@router.post("/{paper_id}/ask")
async def ask_paper_question(
    paper_id: str,
    request: Request,
    body: AskRequest,
    session: AsyncSession = Depends(get_db),
):
    """基于论文全文和用户笔记，用 LLM 回答自然语言问题。"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    from sqlalchemy import select
    from db.models import Paper

    result = await session.execute(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == user["id"])
    )
    paper = result.scalar_one_or_none()
    if not paper:
        return error(msg="论文不存在或无权访问", code=404, data=None, status_code=404)

    notes = await get_notes_by_paper(session, paper_id)

    if not paper.full_text and not notes:
        return error(msg="论文尚未解析且无笔记，暂无内容可供回答", code=400, data=None, status_code=400)

    from app.core.prompts import QA_SYSTEM_PROMPT, build_qa_user_prompt
    from app.core.llm_client import chat_completion

    user_prompt = build_qa_user_prompt(
        title=paper.title,
        authors=paper.authors,
        full_text=paper.full_text,
        notes=notes,
        question=body.question,
        max_chars=settings.QA_MAX_CHARS,
    )

    try:
        answer = await asyncio.to_thread(chat_completion, QA_SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        logger.error("ask_paper LLM error paper_id=%s: %s", paper_id, e)
        return error(msg="AI 服务暂时不可用，请稍后重试", code=503, data=None, status_code=503)

    sources = []
    if paper.full_text:
        excerpt = paper.full_text[:300] + ("…" if len(paper.full_text) > 300 else "")
        sources.append({"type": "full_text", "excerpt": excerpt, "page_number": None})
    for note in notes:
        note_excerpt = note.content[:200] + ("…" if len(note.content) > 200 else "")
        sources.append({"type": "note", "excerpt": note_excerpt, "page_number": note.page_number})

    return success(data={"answer": answer, "sources": sources}, msg="回答成功", code=0, status_code=200)
