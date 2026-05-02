"""
discover.py — 论文发现模块路由

端点：
  GET  /discover/search              关键词检索（Semantic Scholar）
  POST /discover/import              单篇导入（JWT 鉴权，尝试下载 PDF）
  GET  /discover/references/{id}     上游参考文献（含文库标注）
  GET  /discover/citations/{id}      下游引用文献（含文库标注）
"""

import hashlib
import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.core.config import settings
from app.services import semantic_scholar
from app.api.response import ok, err
from db.session import get_session
from db.models import Paper, PaperStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/discover", tags=["discover"])


# ---------------------------------------------------------------------------
# 检索
# ---------------------------------------------------------------------------

@router.get("/search")
def search_papers(
    q: str = Query(..., min_length=1, description="检索关键词"),
    offset: int = Query(0, ge=0, description="分页偏移"),
    limit: int = Query(10, ge=1, le=50, description="每页数量，最大 50"),
    year_from: Optional[int] = Query(None, description="年份下限（含）"),
    year_to: Optional[int] = Query(None, description="年份上限（含）"),
    source_type: Optional[str] = Query(None, description="来源类型：conference | journal | arXiv"),
    sort: str = Query("relevance", description="排序：relevance | citations | date"),
):
    """调用 Semantic Scholar 检索论文，支持年份/来源类型筛选和排序。"""
    logger.info("discover.search q=%r offset=%d limit=%d year=%s-%s source_type=%s sort=%s",
                q, offset, limit, year_from, year_to, source_type, sort)
    try:
        result = semantic_scholar.search_papers(
            q, offset=offset, limit=limit,
            year_from=year_from, year_to=year_to,
            source_type=source_type, sort=sort,
        )
        logger.info("discover.search done total=%d returned=%d", result["total"], len(result["data"]))
        return ok(data=result)
    except RuntimeError as e:
        logger.error("discover.search failed: %s", e)
        return JSONResponse(status_code=502, content=err(502, str(e)))


# ---------------------------------------------------------------------------
# 导入
# ---------------------------------------------------------------------------

class ImportRequest(BaseModel):
    title: str
    authors: Optional[str] = None
    abstract: Optional[str] = None
    doi: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    pdf_url: Optional[str] = None   # Semantic Scholar openAccessPdf.url


@router.post("/import")
async def import_paper(body: ImportRequest, request: Request):
    """单篇导入：从 JWT 获取 user_id，尝试下载 PDF，创建 Paper 记录并触发异步解析。"""
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content=err(401, "未认证"))
    user_id = str(user.id)

    async with get_session() as session:
        if body.doi:
            existing = await session.scalar(
                select(Paper).where(Paper.doi == body.doi, Paper.user_id == user_id)
            )
            if existing:
                logger.warning("discover.import duplicate doi=%s user_id=%s", body.doi, user_id)
                return JSONResponse(status_code=409, content=err(409, "论文已在文库中"))

        # 尝试下载 PDF
        pdf_path, md5_hash, file_size = None, None, 0
        if body.pdf_url:
            try:
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    resp = await client.get(body.pdf_url)
                    resp.raise_for_status()
                content = resp.content
                md5_hash = hashlib.md5(content).hexdigest()
                os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
                pdf_path = os.path.join(settings.UPLOAD_DIR, f"{md5_hash}.pdf")
                if not os.path.exists(pdf_path):
                    with open(pdf_path, "wb") as f:
                        f.write(content)
                file_size = len(content)
                logger.info("discover.import pdf downloaded md5=%s size=%d", md5_hash, file_size)
            except Exception as e:
                logger.warning("discover.import pdf download failed url=%s error=%s", body.pdf_url, e)

        paper = Paper(
            title=body.title, authors=body.authors, abstract=body.abstract,
            doi=body.doi, year=body.year, user_id=user_id,
            pdf_path=pdf_path, md5_hash=md5_hash, file_size=file_size,
            status=PaperStatus.PENDING_PARSING,
        )
        session.add(paper)
        await session.commit()
        await session.refresh(paper)
        logger.info("discover.import paper created paper_id=%s user_id=%s", paper.id, user_id)

    from app.tasks.parse_task import parse_pdf_task
    task = parse_pdf_task.delay(paper.id, pdf_path or "")
    logger.info("discover.import task dispatched task_id=%s paper_id=%s", task.id, paper.id)
    return ok(data={"paper_id": paper.id, "task_id": task.id, "status": paper.status.value})


# ---------------------------------------------------------------------------
# 上下游文献
# ---------------------------------------------------------------------------

@router.get("/references/{semantic_id}")
async def get_references(semantic_id: str, request: Request):
    """获取该论文的参考文献（上游），并标注哪些已在用户文库中。"""
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content=err(401, "未认证"))
    logger.info("discover.references semantic_id=%s user_id=%s", semantic_id, user.id)
    try:
        refs = semantic_scholar.get_references(semantic_id)
    except RuntimeError as e:
        logger.error("discover.references failed: %s", e)
        return JSONResponse(status_code=502, content=err(502, str(e)))
    refs = await _annotate_in_library(refs, str(user.id))
    return ok(data={"data": refs})


@router.get("/citations/{semantic_id}")
async def get_citations(semantic_id: str, request: Request):
    """获取引用该论文的文献（下游），并标注哪些已在用户文库中。"""
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content=err(401, "未认证"))
    logger.info("discover.citations semantic_id=%s user_id=%s", semantic_id, user.id)
    try:
        cites = semantic_scholar.get_citations(semantic_id)
    except RuntimeError as e:
        logger.error("discover.citations failed: %s", e)
        return JSONResponse(status_code=502, content=err(502, str(e)))
    cites = await _annotate_in_library(cites, str(user.id))
    return ok(data={"data": cites})


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

async def _annotate_in_library(papers: list[dict], user_id: str) -> list[dict]:
    """
    批量查询 DOI 是否已在用户文库中，为每条记录添加 in_library 字段。
    无 DOI 的记录直接标记为 False。
    """
    dois = [p["doi"] for p in papers if p.get("doi")]
    if not dois:
        for p in papers:
            p["in_library"] = False
        return papers

    async with get_session() as session:
        rows = await session.scalars(
            select(Paper.doi).where(Paper.doi.in_(dois), Paper.user_id == user_id)
        )
        in_library_dois = set(rows.all())

    logger.debug("_annotate_in_library checked=%d in_library=%d", len(dois), len(in_library_dois))
    for p in papers:
        p["in_library"] = p.get("doi") in in_library_dois
    return papers
