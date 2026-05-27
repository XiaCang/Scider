"""知识图谱：基于论文向量相似度的节点与边（ECharts graph 友好结构）。"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.graph_similarity import build_similarity_edges
from app.core.graph_llm_clustering import generate_llm_graph_structure
from db.crud_graph import list_papers_with_embeddings, list_papers_without_embeddings
from db.models import KeyPoints, Paper, PaperStatus
from db.session import get_db
from utils.response import error, success

router = APIRouter(prefix="/graph", tags=["graph"])


class GraphNodeOut(BaseModel):
    id: str
    name: str
    type: str = "paper"
    category: int = 0
    paperInfo: dict[str, Any] = Field(default_factory=dict)


class GraphLinkOut(BaseModel):
    source: str
    target: str
    relationType: str = "semantic"
    label: Optional[str] = None


class SimilarityGraphOut(BaseModel):
    nodes: list[GraphNodeOut]
    links: list[GraphLinkOut]
    meta: dict[str, Any]


def _build_paper_info(row: dict[str, Any]) -> dict[str, Any]:
    kp = row["key_points"]
    st = row.get("status") or ""
    return {
        "id": row["paper_id"],
        "title": row["title"],
        "authors": row["authors"],
        "year": row["year"],
        "status": _paper_status_from_string(st) if st else "pending_parsing",
        "source": "library",
        "keyPoints": {
            "background": kp.get("background", ""),
            "method": kp.get("method", ""),
            "innovation": kp.get("innovation", ""),
            "conclusion": kp.get("conclusion", ""),
        },
    }


def _paper_status_from_string(s: str) -> str:
    try:
        st = PaperStatus(s)
        return st.name.lower()
    except ValueError:
        return s.lower() if s else "pending_parsing"


@router.get("/similarity", response_model=None)
async def similarity_graph(
    request: Request,
    session: AsyncSession = Depends(get_db),
    folder_id: Optional[str] = Query(None, description="仅包含该文件夹内论文；不传表示用户全部已向量论文"),
    max_nodes: int = Query(200, ge=1, le=200, description="最多节点数（论文篇数），≤200"),
    min_similarity: float = Query(0.55, ge=0.0, le=1.0),
    top_k: int = Query(8, ge=1, le=50, description="每节点保留的最高相似边数"),
):
    """
    返回当前用户文库内、已有向量的论文相似度图。

    - ``max_nodes``: 最多纳入的论文数量（≤200）
    - ``min_similarity``: 连边最低余弦相似度
    - ``top_k``: 每个节点最多保留与其它节点的 top-k 相似连边（去重后截断）
    """
    if folder_id == "":
        folder_id = None

    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    rows = await list_papers_with_embeddings(
        session,
        user["id"],
        folder_id=folder_id,
        max_nodes=max_nodes,
    )

    if len(rows) == 0:
        return success(
            data={
                "nodes": [],
                "links": [],
                "meta": {
                    "paper_count": 0,
                    "reason": "no_embeddings",
                    "embedding_model": settings.EMBEDDING_MODEL,
                },
            },
            msg="ok",
            code=0,
        )

    if len(rows) == 1:
        r = rows[0]
        title = r["title"] or ""
        short = title if len(title) <= 24 else title[:21] + "…"
        single = SimilarityGraphOut(
            nodes=[
                GraphNodeOut(
                    id=r["paper_id"],
                    name=short,
                    type="paper",
                    category=0,
                    paperInfo=_build_paper_info(r),
                )
            ],
            links=[],
            meta={
                "paper_count": 1,
                "edge_count": 0,
                "reason": "need_two_or_more_for_similarity_edges",
                "embedding_model": settings.EMBEDDING_MODEL,
            },
        )
        return success(data=single.model_dump(), msg="ok", code=0)

    paper_ids = [r["paper_id"] for r in rows]
    embeddings = [r["embedding"] for r in rows]

    edge_tuples = build_similarity_edges(
        paper_ids,
        embeddings,
        min_similarity=min_similarity,
        top_k_per_node=top_k,
    )

    nodes_out: list[GraphNodeOut] = []
    for r in rows:
        pid = r["paper_id"]
        title = r["title"] or ""
        short = title if len(title) <= 24 else title[:21] + "…"
        nodes_out.append(
            GraphNodeOut(
                id=pid,
                name=short,
                type="paper",
                category=0,
                paperInfo=_build_paper_info(r),
            )
        )

    links_out = [
        GraphLinkOut(
            source=a,
            target=b,
            relationType="semantic",
            label=f"相似度 {sim:.2f}",
        )
        for a, b, sim in edge_tuples
    ]

    payload = SimilarityGraphOut(
        nodes=nodes_out,
        links=links_out,
        meta={
            "paper_count": len(rows),
            "edge_count": len(links_out),
            "max_nodes": max_nodes,
            "min_similarity": min_similarity,
            "top_k_per_node": top_k,
            "embedding_model": settings.EMBEDDING_MODEL,
        },
    )

    return success(data=payload.model_dump(), msg="ok", code=0)


@router.post("/embeddings/trigger-batch", response_model=None)
async def trigger_batch_embeddings(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """
    对当前用户下已有四要素但尚无向量的论文，批量投递向量化任务。
    用于首次部署向量功能后补发历史论文的向量任务。
    """
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    papers = await list_papers_without_embeddings(session, user["id"])
    if not papers:
        return success(
            data={"triggered": 0, "papers": []},
            msg="所有论文均已生成向量，无需补发",
            code=0,
        )

    from app.tasks.embedding_tasks import embed_paper_task

    triggered: list[dict[str, str]] = []
    for p in papers:
        embed_paper_task.delay(p["paper_id"])
        triggered.append({"paper_id": p["paper_id"], "title": p["title"]})

    return success(
        data={
            "triggered": len(triggered),
            "papers": triggered,
        },
        msg=f"已投递 {len(triggered)} 篇论文的向量化任务",
        code=0,
    )


@router.get("/llm-structure", response_model=None)
async def llm_graph_structure(
    request: Request,
    session: AsyncSession = Depends(get_db),
    folder_id: Optional[str] = Query(None, description="仅包含该文件夹内论文；不传表示用户全部已确认论文"),
    max_nodes: int = Query(50, ge=1, le=100, description="最多节点数（论文篇数），≤100"),
):
    """
    基于 LLM 分析论文四要素，生成主题聚类和语义关系边。

    - 仅包含状态为 CONFIRMED 的论文（已确认四要素）
    - LLM 自动识别研究主题并聚类（2-6 个主题）
    - LLM 生成语义关系边（extends/applies/compares/related）
    - 返回 ECharts graph 友好的节点和边结构，节点按主题分类（category 字段）

    **注意**：此接口调用 LLM，响应时间较长（10-30秒），建议前端设置较长超时。
    """
    if folder_id == "":
        folder_id = None

    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    q = (
        select(Paper, KeyPoints)
        .join(KeyPoints, KeyPoints.paper_id == Paper.id)
        .where(Paper.user_id == user["id"])
        .where(Paper.status == PaperStatus.CONFIRMED)
        .where(KeyPoints.is_confirmed == True)
    )
    if folder_id:
        q = q.where(Paper.folder_id == folder_id)
    q = q.order_by(Paper.updated_at.desc()).limit(max_nodes)

    result = await session.execute(q)
    rows = result.all()

    if len(rows) == 0:
        return success(
            data={
                "nodes": [],
                "links": [],
                "clusters": [],
                "meta": {
                    "paper_count": 0,
                    "reason": "no_confirmed_papers",
                    "message": "没有已确认的论文，请先确认论文四要素",
                },
            },
            msg="ok",
            code=0,
        )

    papers_for_llm: list[dict[str, Any]] = []
    paper_map: dict[str, tuple[Paper, KeyPoints]] = {}

    for paper, kp in rows:
        paper_map[paper.id] = (paper, kp)
        papers_for_llm.append({
            "paper_id": paper.id,
            "title": paper.title or "",
            "authors": paper.authors or "",
            "year": paper.year if paper.year is not None else 0,
            "key_points": {
                "background": kp.background or "",
                "method": kp.methodology or "",
                "innovation": kp.innovation or "",
                "conclusion": kp.conclusion or "",
            },
        })

    if len(papers_for_llm) == 1:
        p = papers_for_llm[0]
        paper, kp = paper_map[p["paper_id"]]
        title = paper.title or ""
        short = title if len(title) <= 24 else title[:21] + "…"
        return success(
            data={
                "nodes": [
                    GraphNodeOut(
                        id=paper.id,
                        name=short,
                        type="paper",
                        category=0,
                        paperInfo={
                            "id": paper.id,
                            "title": paper.title,
                            "authors": paper.authors,
                            "year": paper.year,
                            "status": "confirmed",
                            "source": "library",
                            "keyPoints": {
                                "background": kp.background or "",
                                "method": kp.methodology or "",
                                "innovation": kp.innovation or "",
                                "conclusion": kp.conclusion or "",
                            },
                        },
                    ).model_dump()
                ],
                "links": [],
                "clusters": [
                    {
                        "id": "cluster_0",
                        "name": "单篇论文",
                        "description": "仅有一篇论文，无需聚类",
                        "paper_ids": [paper.id],
                    }
                ],
                "meta": {
                    "paper_count": 1,
                    "cluster_count": 1,
                    "edge_count": 0,
                    "reason": "single_paper",
                },
            },
            msg="ok",
            code=0,
        )

    try:
        llm_result = generate_llm_graph_structure(papers_for_llm)
    except Exception as e:
        return error(
            msg=f"LLM 图结构生成失败: {str(e)}",
            code=500,
            data=None,
            status_code=500,
        )

    cluster_map: dict[str, int] = {}
    for idx, cluster in enumerate(llm_result.clusters):
        for pid in cluster["paper_ids"]:
            cluster_map[pid] = idx

    nodes_out: list[GraphNodeOut] = []
    for p in papers_for_llm:
        pid = p["paper_id"]
        paper, kp = paper_map[pid]
        title = paper.title or ""
        short = title if len(title) <= 24 else title[:21] + "…"
        category = cluster_map.get(pid, 0)

        nodes_out.append(
            GraphNodeOut(
                id=pid,
                name=short,
                type="paper",
                category=category,
                paperInfo={
                    "id": paper.id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "year": paper.year,
                    "status": "confirmed",
                    "source": "library",
                    "keyPoints": {
                        "background": kp.background or "",
                        "method": kp.methodology or "",
                        "innovation": kp.innovation or "",
                        "conclusion": kp.conclusion or "",
                    },
                },
            )
        )

    relation_type_map = {
        "extends": "扩展",
        "applies": "应用",
        "compares": "对比",
        "related": "相关",
    }

    links_out = [
        GraphLinkOut(
            source=edge["source"],
            target=edge["target"],
            relationType=edge["relation_type"],
            label=f"{relation_type_map.get(edge['relation_type'], '相关')}: {edge['reason']}",
        )
        for edge in llm_result.edges
    ]

    payload = {
        "nodes": [n.model_dump() for n in nodes_out],
        "links": [l.model_dump() for l in links_out],
        "clusters": llm_result.clusters,
        "meta": {
            "paper_count": len(papers_for_llm),
            "cluster_count": len(llm_result.clusters),
            "edge_count": len(links_out),
            "max_nodes": max_nodes,
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.DEEPSEEK_MODEL if settings.LLM_PROVIDER == "deepseek" else settings.QWEN_MODEL,
        },
    }

    return success(data=payload, msg="ok", code=0)
