import hashlib
import os

import aiofiles
from fastapi import APIRouter, Depends, File, Request, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from db.crud_keypoints import save_confirmed_key_points
from db.crud_paper import create_paper, get_paper_by_md5
from db.session import get_db
from utils.response import success, error

router = APIRouter(prefix="/papers", tags=["papers"])


class KeyPointsIn(BaseModel):
    background: str = ""
    method: str = ""
    innovation: str = ""
    conclusion: str = ""


class PatchKeyPointsBody(BaseModel):
    """与前端 `saveKeyPointsApi` 一致：{ keyPoints: { background, method, ... } }"""

    model_config = ConfigDict(populate_by_name=True)
    key_points: KeyPointsIn = Field(alias="keyPoints")

ALLOWED_EXTENSIONS = {".pdf"}


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
        and kp.method.strip()
        and kp.innovation.strip()
        and kp.conclusion.strip()
    ):
        return error(msg="四要素均需填写非空内容", code=400, data=None, status_code=200)

    paper, err = await save_confirmed_key_points(
        session,
        paper_id,
        user["id"],
        background=kp.background,
        method=kp.method,
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
