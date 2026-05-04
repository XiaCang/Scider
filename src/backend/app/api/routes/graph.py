"""知识图谱：基于论文向量相似度的节点与边（ECharts graph 友好结构）。"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.graph_similarity import build_similarity_edges
from db.crud_graph import list_papers_with_embeddings
from db.models import PaperStatus
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
