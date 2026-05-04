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
from typing import Optional, List

import httpx
from fastapi import APIRouter, Query, Request, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.config import settings
from app.services import semantic_scholar
from app.api.response import ok, err
from db.session import get_session
from db.models import Paper, PaperStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/discover", tags=["论文发现"])


# ---------------------------------------------------------------------------
# 响应模型
# ---------------------------------------------------------------------------

class PaperItem(BaseModel):
    """论文条目"""
    semantic_id: Optional[str] = Field(None, description="Semantic Scholar 论文 ID")
    title: Optional[str] = Field(None, description="论文标题")
    authors: Optional[str] = Field(None, description="作者列表（逗号分隔）")
    year: Optional[int] = Field(None, description="发表年份")
    venue: Optional[str] = Field(None, description="发表会议/期刊")
    source_type: Optional[str] = Field(None, description="来源类型：conference | journal | arXiv | other")
    abstract: Optional[str] = Field(None, description="摘要")
    doi: Optional[str] = Field(None, description="DOI")
    citation_count: Optional[int] = Field(None, description="引用次数")
    pdf_url: Optional[str] = Field(None, description="开放获取 PDF 链接")
    in_library: Optional[bool] = Field(None, description="是否已在用户文库中（仅上下游接口返回）")


class SearchResponse(BaseModel):
    """检索响应"""
    total: int = Field(..., description="总结果数")
    offset: int = Field(..., description="当前偏移量")
    limit: int = Field(..., description="每页数量")
    data: List[PaperItem] = Field(..., description="论文列表")


class ImportResponse(BaseModel):
    """导入响应"""
    paper_id: str = Field(..., description="论文 ID")
    task_id: str = Field(..., description="异步解析任务 ID")
    status: str = Field(..., description="论文状态")


# ---------------------------------------------------------------------------
# 检索
# ---------------------------------------------------------------------------

@router.get(
    "/search",
    summary="检索论文",
    description="调用 Semantic Scholar API 进行关键词检索，支持年份、来源类型筛选和多种排序方式",
    response_model=None,
    responses={
        200: {"description": "检索成功"},
        502: {"description": "Semantic Scholar API 调用失败"}
    }
)
def search_papers(
    q: str = Query(..., min_length=1, description="检索关键词"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    limit: int = Query(10, ge=1, le=50, description="每页数量，最大 50"),
    year_from: Optional[int] = Query(None, description="年份下限（含）"),
    year_to: Optional[int] = Query(None, description="年份上限（含）"),
    source_type: Optional[str] = Query(None, description="来源类型筛选", enum=["conference", "journal", "arXiv"]),
    sort: str = Query("relevance", description="排序方式", enum=["relevance", "citations", "date"]),
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
    """导入论文请求体"""
    title: str = Field(..., description="论文标题")
    authors: Optional[str] = Field(None, description="作者列表（逗号分隔）")
    abstract: Optional[str] = Field(None, description="摘要")
    doi: Optional[str] = Field(None, description="DOI")
    year: Optional[int] = Field(None, description="发表年份")
    venue: Optional[str] = Field(None, description="发表会议/期刊")
    pdf_url: Optional[str] = Field(None, description="PDF 下载链接")


@router.post(
    "/import",
    summary="导入论文到文库",
    description="将检索到的论文导入到用户文库，自动下载 PDF（如有）并触发异步解析任务",
    response_model=None,
    responses={
        200: {"description": "导入成功"},
        401: {"description": "未认证"},
        409: {"description": "论文已存在于文库中"}
    }
)
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

@router.get(
    "/references/{semantic_id}",
    summary="获取参考文献",
    description="获取指定论文的参考文献列表（该论文引用的文献，即上游），并标注哪些已在用户文库中",
    response_model=None,
    responses={
        200: {"description": "获取成功"},
        401: {"description": "未认证"},
        502: {"description": "Semantic Scholar API 调用失败"}
    }
)
async def get_references(
    semantic_id: str = Path(..., description="Semantic Scholar 论文 ID"),
    request: Request = None
):
    """获取该论文的参考文献（上游），并标注哪些已在用户文库中。"""
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content=err(401, "未认证"))
    user_id = str(user.id)
    logger.info("discover.references semantic_id=%s user_id=%s", semantic_id, user_id)
    try:
        refs = semantic_scholar.get_references(semantic_id)
    except RuntimeError as e:
        logger.error("discover.references failed: %s", e)
        return JSONResponse(status_code=502, content=err(502, str(e)))
    refs = await _annotate_in_library(refs, str(user_id))
    return ok(data={"data": refs})


@router.get(
    "/citations/{semantic_id}",
    summary="获取引用文献",
    description="获取引用指定论文的文献列表（下游），并标注哪些已在用户文库中",
    response_model=None,
    responses={
        200: {"description": "获取成功"},
        401: {"description": "未认证"},
        502: {"description": "Semantic Scholar API 调用失败"}
    }
)
async def get_citations(
    semantic_id: str = Path(..., description="Semantic Scholar 论文 ID"),
    request: Request = None
):
    """获取引用该论文的文献（下游），并标注哪些已在用户文库中。"""
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content=err(401, "未认证"))
    user_id = str(user.id)
    logger.info("discover.citations semantic_id=%s user_id=%s", semantic_id, user_id)
    try:
        cites = semantic_scholar.get_citations(semantic_id)
    except RuntimeError as e:
        logger.error("discover.citations failed: %s", e)
        return JSONResponse(status_code=502, content=err(502, str(e)))
    cites = await _annotate_in_library(cites, str(user_id))
    return ok(data={"data": cites})


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

async def _annotate_in_library(papers: list[dict], user_id: str) -> list[dict]:
    """批量查询 DOI 是否已在用户文库中，为每条记录添加 in_library 字段。"""
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
