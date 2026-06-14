"""
discover.py — 论文发现模块路由

端点：
  GET  /discover/search              关键词检索（Semantic Scholar）
  POST /discover/import              单篇导入（JWT 鉴权，尝试下载 PDF）
  GET  /discover/references/{id}     上游参考文献（含文库标注）
  GET  /discover/citations/{id}      下游引用文献（含文库标注）
  GET  /discover/pdf-proxy           代理下载外部 PDF（避免 CORS）
"""

import asyncio
import hashlib
import logging
import os
from typing import Optional, List

import httpx
from fastapi import APIRouter, Query, Request, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select

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
    arxiv_id: Optional[str] = Field(None, description="arXiv ID")
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
async def search_papers(
    request: Request,
    q: str = Query(..., min_length=1, description="检索关键词"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    limit: int = Query(10, ge=1, le=50, description="每页数量，最大 50"),
    year_from: Optional[int] = Query(None, description="年份下限（含）"),
    year_to: Optional[int] = Query(None, description="年份上限（含）"),
    source_type: Optional[str] = Query(None, description="来源类型筛选", enum=["conference", "journal", "arXiv"]),
    sort: str = Query("relevance", description="排序方式", enum=["relevance", "citations", "date"]),
):
    """调用 Semantic Scholar 检索论文，支持年份/来源类型筛选和排序，标注文库状态。"""
    logger.info("discover.search q=%r offset=%d limit=%d year=%s-%s source_type=%s sort=%s",
                q, offset, limit, year_from, year_to, source_type, sort)
    try:
        result = await asyncio.to_thread(
            semantic_scholar.search_papers,
            q, offset=offset, limit=limit,
            year_from=year_from, year_to=year_to,
            source_type=source_type, sort=sort,
        )
        # 标注已在文库中的论文
        user = getattr(request.state, "user", None)
        if user:
            result["data"] = await _annotate_in_library(result["data"], str(user["id"]))
        logger.info("discover.search done total=%d returned=%d", result["total"], len(result["data"]))
        return ok(data=result)
    except RuntimeError as e:
        logger.error("discover.search failed: %s", e)
        return JSONResponse(status_code=502, content=err(502, str(e)))


# ---------------------------------------------------------------------------
# 推荐
# ---------------------------------------------------------------------------

@router.get(
    "/recommendations",
    summary="获取论文推荐",
    description="基于用户文库中的论文，通过 Semantic Scholar 搜索相似论文进行推荐",
    response_model=None,
)
async def get_recommendations(
    request: Request,
    direction: str = Query("", description="推荐方向（预留）"),
):
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content=err(401, "未认证"))
    user_id = str(user["id"])
    logger.info("discover.recommendations user_id=%s direction=%s", user_id, direction)

    # 获取用户文库中最近 3 篇论文
    async with get_session() as session:
        rows = await session.execute(
            select(Paper)
            .where(Paper.user_id == user_id)
            .order_by(Paper.created_at.desc())
            .limit(3)
        )
        papers = rows.scalars().all()

    if not papers:
        logger.info("discover.recommendations 文库为空 user_id=%s", user_id)
        return ok(data=[])

    # 按标题搜索 SS，收集推荐结果
    seen_semantic_ids: set[str] = set()
    results: list[dict] = []
    for paper in papers:
        if not paper.title:
            continue
        try:
            result = await asyncio.to_thread(
                semantic_scholar.search_papers, paper.title, 0, 4
            )
            for p in result.get("data", []):
                sid = p.get("semantic_id")
                if sid and sid not in seen_semantic_ids:
                    seen_semantic_ids.add(sid)
                    p["reason"] = f"相似于「{paper.title[:40]}」"
                    results.append(p)
        except RuntimeError as e:
            logger.warning("discover.recommendations search failed title=%s err=%s", paper.title[:40], e)
            continue

    results = await _annotate_in_library(results, user_id)
    logger.info("discover.recommendations done user_id=%s count=%d", user_id, len(results))
    return ok(data=results)


# ---------------------------------------------------------------------------
# 导入
# ---------------------------------------------------------------------------

class ImportRequest(BaseModel):
    """导入论文请求体"""
    title: str = Field(..., description="论文标题")
    authors: Optional[str] = Field(None, description="作者列表（逗号分隔）")
    abstract: Optional[str] = Field(None, description="摘要")
    doi: Optional[str] = Field(None, description="DOI")
    arxiv_id: Optional[str] = Field(None, description="arXiv ID")
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
    user_id = str(user["id"])

    async with get_session() as session:
        if body.doi:
            existing = await session.scalar(
                select(Paper).where(Paper.doi == body.doi, Paper.user_id == user_id)
            )
            if existing:
                logger.warning("discover.import duplicate doi=%s user_id=%s", body.doi, user_id)
                return JSONResponse(status_code=409, content=err(409, "论文已在文库中"))

        pdf_path, md5_hash, file_size = None, None, 0
        # 收集所有可用的 PDF 下载链接：arXiv PDF 优先，其次 OA PDF
        pdf_urls_to_try: list[str] = []
        if body.arxiv_id:
            pdf_urls_to_try.append(f"https://arxiv.org/pdf/{body.arxiv_id}.pdf")
        if body.pdf_url:
            pdf_urls_to_try.append(body.pdf_url)

        for url in pdf_urls_to_try:
            try:
                async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                    resp = await client.get(url)
                    resp.raise_for_status()
                content = resp.content
                md5_hash = hashlib.md5(content).hexdigest()
                os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
                pdf_path = os.path.join(settings.UPLOAD_DIR, f"{md5_hash}.pdf")
                if not os.path.exists(pdf_path):
                    with open(pdf_path, "wb") as f:
                        f.write(content)
                file_size = len(content)
                logger.info("discover.import pdf downloaded url=%s md5=%s size=%d", url, md5_hash, file_size)
                break  # 下载成功就退出循环
            except Exception as e:
                logger.warning("discover.import pdf download failed url=%s error=%s", url, e)

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

    # 有 PDF 才派发解析任务；仅导入元数据的论文等待后续 PDF 上传
    if pdf_path:
        from app.tasks.parse_task import parse_pdf_task
        task = parse_pdf_task.delay(paper.id, pdf_path)
        logger.info("discover.import task dispatched task_id=%s paper_id=%s", task.id, paper.id)
        return ok(data={"paper_id": paper.id, "task_id": task.id, "status": paper.status.value})
    else:
        logger.info("discover.import no pdf_url, paper created without parse task paper_id=%s", paper.id)
        return ok(data={"paper_id": paper.id, "task_id": None, "status": paper.status.value})


# ---------------------------------------------------------------------------
# PDF 代理下载
# ---------------------------------------------------------------------------

@router.get(
    "/pdf-proxy",
    summary="代理下载外部 PDF",
    description="通过后端代理下载外部 PDF（避免前端跨域限制），要求用户已认证",
)
async def proxy_pdf(
    request: Request,
    pdf_url: str = Query(..., description="需要下载的 PDF 链接"),
):
    """代理下载外部 PDF 文件，避免前端直接请求外部资源时的跨域问题。"""
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content=err(401, "未认证"))

    logger.info("discover.pdf_proxy user_id=%s pdf_url=%s", str(user["id"]), pdf_url[:120])

    # 模拟常见浏览器请求头，避免被目标网站（如 AIP、IEEE 等）拒绝
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Referer": pdf_url.rsplit("/", 1)[0] + "/",
    }

    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(pdf_url, headers=headers)
            resp.raise_for_status()
        content = resp.content

        # 从 URL 中提取文件名
        filename = os.path.basename(pdf_url.split("?")[0])
        if not filename.endswith(".pdf"):
            filename = "paper.pdf"

        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(content)),
            },
        )
    except httpx.TimeoutException:
        logger.error("discover.pdf_proxy timeout url=%s", pdf_url[:120])
        return JSONResponse(status_code=504, content=err(504, "下载 PDF 超时"))
    except Exception as e:
        logger.error("discover.pdf_proxy failed url=%s error=%s", pdf_url[:120], e)
        return JSONResponse(status_code=502, content=err(502, f"下载 PDF 失败: {str(e)}"))


# ---------------------------------------------------------------------------
# 上下游文献
# ---------------------------------------------------------------------------

@router.get(
    "/references/by-paper/{paper_id}",
    summary="根据本地论文 ID 获取参考文献",
    description="根据本地论文 ID 查找 DOI 后调用 Semantic Scholar 获取参考文献（上游）",
    response_model=None,
)
async def get_references_by_paper(
    paper_id: str = Path(..., description="本地论文 ID"),
    request: Request = None,
):
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content=err(401, "未认证"))
    user_id = str(user["id"])
    logger.info("discover.references.by_paper paper_id=%s user_id=%s", paper_id, user_id)
    async with get_session() as session:
        paper = await session.scalar(
            select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
        )
        if not paper:
            return JSONResponse(status_code=404, content=err(404, "论文不存在"))
    semantic_id = await _resolve_semantic_id(paper)
    if not semantic_id:
        return JSONResponse(status_code=404, content=err(404, "无法确定论文的 Semantic Scholar ID"))
    try:
        refs = await asyncio.to_thread(semantic_scholar.get_references, semantic_id)
    except RuntimeError as e:
        logger.error("discover.references.by_paper failed: %s", e)
        return JSONResponse(status_code=502, content=err(502, str(e)))
    refs = await _annotate_in_library(refs, user_id)
    return ok(data={"data": refs})


@router.get(
    "/citations/by-paper/{paper_id}",
    summary="根据本地论文 ID 获取引用文献",
    description="根据本地论文 ID 查找 DOI 后调用 Semantic Scholar 获取引用文献（下游）",
    response_model=None,
)
async def get_citations_by_paper(
    paper_id: str = Path(..., description="本地论文 ID"),
    request: Request = None,
):
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content=err(401, "未认证"))
    user_id = str(user["id"])
    logger.info("discover.citations.by_paper paper_id=%s user_id=%s", paper_id, user_id)
    async with get_session() as session:
        paper = await session.scalar(
            select(Paper).where(Paper.id == paper_id, Paper.user_id == user_id)
        )
        if not paper:
            return JSONResponse(status_code=404, content=err(404, "论文不存在"))
    semantic_id = await _resolve_semantic_id(paper)
    if not semantic_id:
        return JSONResponse(status_code=404, content=err(404, "无法确定论文的 Semantic Scholar ID"))
    try:
        cites = await asyncio.to_thread(semantic_scholar.get_citations, semantic_id)
    except RuntimeError as e:
        logger.error("discover.citations.by_paper failed: %s", e)
        return JSONResponse(status_code=502, content=err(502, str(e)))
    cites = await _annotate_in_library(cites, user_id)
    return ok(data={"data": cites})

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
    user_id = str(user["id"])
    logger.info("discover.references semantic_id=%s user_id=%s", semantic_id, user_id)
    try:
        refs = await asyncio.to_thread(semantic_scholar.get_references, semantic_id)
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
    user_id = str(user["id"])
    logger.info("discover.citations semantic_id=%s user_id=%s", semantic_id, user_id)
    try:
        cites = await asyncio.to_thread(semantic_scholar.get_citations, semantic_id)
    except RuntimeError as e:
        logger.error("discover.citations failed: %s", e)
        return JSONResponse(status_code=502, content=err(502, str(e)))
    cites = await _annotate_in_library(cites, str(user_id))
    return ok(data={"data": cites})


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

async def _resolve_semantic_id(paper) -> str | None:
    """从论文记录解析出 Semantic Scholar ID，优先用 DOI，否则按标题搜索。"""
    if paper.doi:
        return f"DOI:{paper.doi}"
    if paper.title:
        logger.info("_resolve_semantic_id 论文无 DOI，按标题搜索 paper_id=%s title=%r", paper.id, paper.title[:60])
        try:
            result = await asyncio.to_thread(semantic_scholar.search_papers, paper.title, 0, 3)
            papers = result.get("data", [])
            if papers:
                s2_id = papers[0].get("semantic_id") or papers[0].get("paperId")
                if s2_id:
                    logger.info("_resolve_semantic_id 搜索命中 paper_id=%s s2_id=%s", paper.id, s2_id)
                    return s2_id
        except Exception as e:
            logger.warning("_resolve_semantic_id 搜索失败 paper_id=%s error=%s", paper.id, e)
    return None


async def _annotate_in_library(papers: list[dict], user_id: str) -> list[dict]:
    """批量查询论文（按 DOI 或标题）是否已在用户文库中，为每条记录添加 in_library 字段。"""
    # 1. 收集有 DOI 的论文，批量查询
    dois = [p["doi"] for p in papers if p.get("doi")]
    in_library_dois: set[str] = set()
    if dois:
        async with get_session() as session:
            rows = await session.scalars(
                select(Paper.doi).where(Paper.doi.in_(dois), Paper.user_id == user_id)
            )
            in_library_dois = set(rows.all())

    # 2. 收集无 DOI 的论文标题，按标题匹配
    no_doi_titles = [
        (i, p["title"]) for i, p in enumerate(papers)
        if not p.get("doi") and p.get("title")
    ]
    in_library_by_title: set[int] = set()
    if no_doi_titles:
        title_list = [t for _, t in no_doi_titles]
        from sqlalchemy import func
        async with get_session() as session:
            rows = await session.execute(
                select(Paper.title).where(
                    func.lower(Paper.title).in_([t.lower() for t in title_list]),
                    Paper.user_id == user_id,
                )
            )
            matched_titles = {r[0].lower() for r in rows.all()}
        for i, title in no_doi_titles:
            if title.lower() in matched_titles:
                in_library_by_title.add(i)

    logger.debug(
        "_annotate_in_library dois=%d matched=%d titles=%d matched=%d",
        len(dois), len(in_library_dois),
        len(no_doi_titles), len(in_library_by_title),
    )
    for i, p in enumerate(papers):
        p["in_library"] = (
            p.get("doi") in in_library_dois
            or i in in_library_by_title
        )
    return papers
