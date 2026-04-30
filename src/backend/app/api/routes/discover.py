"""
discover.py — 论文发现模块路由

端点：
  GET  /discover/search              关键词检索（Semantic Scholar）
  POST /discover/import              单篇导入
  POST /discover/import/bulk         批量导入（上限 20 篇）
  GET  /discover/references/{id}     上游参考文献（含文库标注）
  GET  /discover/citations/{id}      下游引用文献（含文库标注）
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.services import semantic_scholar
from app.tasks.paper_tasks import parse_paper_task
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
    user_id: str


@router.post("/import")
async def import_paper(body: ImportRequest):
    """
    单篇导入：创建 Paper 记录并触发异步解析任务。
    若同一用户已存在相同 DOI 的论文，返回 409。
    """
    logger.info("discover.import title=%r doi=%s user_id=%s", body.title, body.doi, body.user_id)
    async with get_session() as session:
        # 按 DOI 去重（仅当 DOI 存在时检查）
        if body.doi:
            existing = await session.scalar(
                select(Paper).where(Paper.doi == body.doi, Paper.user_id == body.user_id)
            )
            if existing:
                logger.warning("discover.import duplicate doi=%s user_id=%s", body.doi, body.user_id)
                return JSONResponse(status_code=409, content=err(409, "论文已在文库中"))

        paper = Paper(
            title=body.title, authors=body.authors, abstract=body.abstract,
            doi=body.doi, year=body.year, user_id=body.user_id,
            status=PaperStatus.PENDING_PARSING,
        )
        session.add(paper)
        await session.commit()
        await session.refresh(paper)
        logger.info("discover.import paper created paper_id=%s", paper.id)

    task = parse_paper_task.delay(paper.id)
    logger.info("discover.import task dispatched task_id=%s paper_id=%s", task.id, paper.id)
    return ok(data={"paper_id": paper.id, "task_id": task.id, "status": paper.status.value})


class BulkImportRequest(BaseModel):
    papers: list[ImportRequest]
    user_id: str


@router.post("/import/bulk")
async def bulk_import_papers(body: BulkImportRequest):
    """
    批量导入，单次上限 20 篇。
    逐篇检查重复，跳过已存在的论文；其余逐篇创建记录并派发 Celery 任务。
    使用 flush() 在单个事务内获取 paper.id，最后统一 commit。
    """
    if len(body.papers) > 20:
        logger.warning("discover.bulk_import count=%d exceeds limit", len(body.papers))
        return JSONResponse(status_code=400, content=err(400, "单次批量导入上限为 20 篇"))

    logger.info("discover.bulk_import count=%d user_id=%s", len(body.papers), body.user_id)
    results = []
    async with get_session() as session:
        for item in body.papers:
            item.user_id = body.user_id

            if item.doi:
                existing = await session.scalar(
                    select(Paper).where(Paper.doi == item.doi, Paper.user_id == body.user_id)
                )
                if existing:
                    logger.debug("bulk_import skip duplicate doi=%s", item.doi)
                    results.append({"title": item.title, "skipped": True, "reason": "论文已在文库中"})
                    continue

            paper = Paper(
                title=item.title, authors=item.authors, abstract=item.abstract,
                doi=item.doi, year=item.year, user_id=body.user_id,
                status=PaperStatus.PENDING_PARSING,
            )
            session.add(paper)
            await session.flush()  # 获取 paper.id，不提交事务
            task = parse_paper_task.delay(paper.id)
            logger.debug("bulk_import queued paper_id=%s task_id=%s", paper.id, task.id)
            results.append({"paper_id": paper.id, "task_id": task.id, "skipped": False})

        await session.commit()

    imported = sum(1 for r in results if not r.get("skipped"))
    logger.info("discover.bulk_import done imported=%d skipped=%d", imported, len(results) - imported)
    return ok(data={"results": results})


# ---------------------------------------------------------------------------
# 上下游文献
# ---------------------------------------------------------------------------

@router.get("/references/{semantic_id}")
async def get_references(semantic_id: str, user_id: str = Query(..., description="当前用户 ID")):
    """获取该论文的参考文献（上游），并标注哪些已在用户文库中。"""
    logger.info("discover.references semantic_id=%s user_id=%s", semantic_id, user_id)
    try:
        refs = semantic_scholar.get_references(semantic_id)
    except RuntimeError as e:
        logger.error("discover.references failed: %s", e)
        return JSONResponse(status_code=502, content=err(502, str(e)))

    refs = await _annotate_in_library(refs, user_id)
    return ok(data={"data": refs})


@router.get("/citations/{semantic_id}")
async def get_citations(semantic_id: str, user_id: str = Query(..., description="当前用户 ID")):
    """获取引用该论文的文献（下游），并标注哪些已在用户文库中。"""
    logger.info("discover.citations semantic_id=%s user_id=%s", semantic_id, user_id)
    try:
        cites = semantic_scholar.get_citations(semantic_id)
    except RuntimeError as e:
        logger.error("discover.citations failed: %s", e)
        return JSONResponse(status_code=502, content=err(502, str(e)))

    cites = await _annotate_in_library(cites, user_id)
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
