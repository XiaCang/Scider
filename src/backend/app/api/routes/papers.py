"""
papers.py — 论文文件管理路由

端点：
  POST /papers/{paper_id}/upload   上传 PDF 文件，保存到磁盘并触发解析任务
"""

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api.response import ok, err
from app.core.config import settings
from app.tasks.paper_tasks import parse_paper_task
from db.session import get_session
from db.models import Paper, PaperStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/papers", tags=["papers"])

_ALLOWED_CONTENT_TYPES = {"application/pdf"}
_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/{paper_id}/upload")
async def upload_paper_pdf(paper_id: str, file: UploadFile = File(...)):
    """
    上传论文 PDF 文件。

    - 校验文件类型（必须为 application/pdf）
    - 将文件保存到 UPLOAD_DIR/{paper_id}.pdf
    - 更新 Paper.pdf_path 并将状态重置为 PENDING_PARSING
    - 派发 parse_paper_task 异步任务

    Args:
        paper_id: Paper 表主键，路径参数。
        file:     multipart/form-data 上传的 PDF 文件。

    Returns:
        {"paper_id": ..., "task_id": ..., "pdf_path": ...}
    """
    # 1. 校验 Content-Type
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        logger.warning(
            "upload_paper_pdf rejected content_type=%s paper_id=%s",
            file.content_type, paper_id,
        )
        return JSONResponse(
            status_code=415,
            content=err(415, f"仅支持 PDF 文件，收到: {file.content_type}"),
        )

    # 2. 确认 Paper 记录存在
    async with get_session() as session:
        paper = await session.get(Paper, paper_id)
        if paper is None:
            logger.warning("upload_paper_pdf paper not found paper_id=%s", paper_id)
            raise HTTPException(status_code=404, detail="论文记录不存在")

    # 3. 保存文件到磁盘
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest_path = upload_dir / f"{paper_id}.pdf"

    try:
        with dest_path.open("wb") as out:
            # 分块读取，避免大文件占满内存
            total = 0
            while chunk := await file.read(1024 * 256):  # 256 KB chunks
                total += len(chunk)
                if total > _MAX_FILE_SIZE:
                    out.close()
                    dest_path.unlink(missing_ok=True)
                    logger.warning(
                        "upload_paper_pdf file too large paper_id=%s size>%d",
                        paper_id, _MAX_FILE_SIZE,
                    )
                    return JSONResponse(
                        status_code=413,
                        content=err(413, "文件超过 50 MB 限制"),
                    )
                out.write(chunk)
    except OSError as e:
        logger.exception("upload_paper_pdf write failed paper_id=%s", paper_id)
        return JSONResponse(status_code=500, content=err(500, f"文件保存失败: {e}"))

    logger.info(
        "upload_paper_pdf saved paper_id=%s path=%s size=%d",
        paper_id, dest_path, total,
    )

    # 4. 更新数据库：写入 pdf_path，重置状态为 PENDING_PARSING
    async with get_session() as session:
        paper = await session.get(Paper, paper_id)
        paper.pdf_path = str(dest_path)
        paper.status = PaperStatus.PENDING_PARSING
        await session.commit()
        logger.debug(
            "upload_paper_pdf db updated paper_id=%s pdf_path=%s", paper_id, dest_path
        )

    # 5. 派发解析任务
    task = parse_paper_task.delay(paper_id)
    logger.info(
        "upload_paper_pdf task dispatched task_id=%s paper_id=%s",
        task.id, paper_id,
    )

    return ok(data={
        "paper_id": paper_id,
        "task_id": task.id,
        "pdf_path": str(dest_path),
    })
