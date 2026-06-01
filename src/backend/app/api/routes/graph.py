"""知识图谱：基于论文向量相似度的节点与边（ECharts graph 友好结构）。"""

import hashlib
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.graph_similarity import build_similarity_edges
from app.core.graph_llm_clustering import generate_llm_graph_structure
from db.crud_graph import list_papers_with_embeddings, list_papers_without_embeddings
from db.models import KeyPoints, Paper, PaperStatus, GraphNode, GraphEdge, GraphLLMCache
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
    min_similarity: float = Query(0.4, ge=0.0, le=1.0),
    top_k: int = Query(8, ge=1, le=50, description="每节点保留的最高相似边数"),
):
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


# ---------- 辅助函数：缓存键生成 ----------
def _papers_hash(paper_ids: list[str]) -> str:
    sorted_ids = sorted(paper_ids)
    return hashlib.md5(",".join(sorted_ids).encode()).hexdigest()


# ---------- 辅助函数：合并自定义节点 ----------
async def _merge_custom_nodes(
    session: AsyncSession,
    user_id: str,
    raw_nodes: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """合并用户自定义节点：仅合并纯自定义节点（paper_id 为 NULL），
    系统论文节点和自动创建的覆盖节点不被合并，保留系统原始数据。"""
    # 只查询 paper_id 为 NULL 的纯自定义节点
    q = select(GraphNode).where(GraphNode.user_id == user_id, GraphNode.paper_id.is_(None))
    custom_nodes = (await session.execute(q)).scalars().all()

    # 建立 id -> custom node 映射
    id_map = {n.id: n for n in custom_nodes}

    result = []
    for raw in raw_nodes:
        node_id = raw["id"]
        custom = id_map.get(node_id)
        if custom:
            # 覆盖名称、类型、分类
            raw["name"] = custom.name
            raw["category"] = custom.category
            raw["type"] = custom.node_type
        result.append(raw)

    # 添加纯自定义节点（id 不在原始节点中的）
    existing_ids = {n["id"] for n in result}
    for custom in custom_nodes:
        if custom.id not in existing_ids:
            result.append({
                "id": custom.id,
                "name": custom.name,
                "type": custom.node_type,
                "category": custom.category,
                "paperInfo": custom.properties or {},
            })
    return result


async def _merge_custom_edges(
    session: AsyncSession,
    user_id: str,
    raw_edges: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """合并用户自定义边：如果存在 GraphEdge 且匹配系统边则覆盖；添加纯自定义边"""
    q = select(GraphEdge).where(GraphEdge.user_id == user_id)
    custom_edges = (await session.execute(q)).scalars().all()

    # 建立系统边的唯一标识 (source, target, relation_type) 的映射
    edge_map = {}
    for ce in custom_edges:
        key = (ce.source_id, ce.target_id, ce.relation_type)
        edge_map[key] = ce

    result = []
    for raw in raw_edges:
        key = (raw["source"], raw["target"], raw.get("relationType", "semantic"))
        custom = edge_map.get(key)
        if custom:
            raw["label"] = custom.label or raw.get("label")
            raw["relationType"] = custom.relation_type
        # 为每条边生成一个唯一 id（用于前端编辑），格式 edge_{source}_{target}_{relation_type}
        raw["id"] = f"edge_{raw['source']}_{raw['target']}_{raw.get('relationType', 'semantic')}"
        result.append(raw)

    # 添加纯粹的自定义边（未在原始边中存在的）
    existing_keys = {(e["source"], e["target"]) for e in result}
    for custom in custom_edges:
        if (custom.source_id, custom.target_id) not in existing_keys:
            result.append({
                "id": f"edge_{custom.source_id}_{custom.target_id}_{custom.relation_type}",
                "source": custom.source_id,
                "target": custom.target_id,
                "relationType": custom.relation_type,
                "label": custom.label,
            })
    return result


@router.get("/llm-structure", response_model=None)
async def llm_graph_structure(
    request: Request,
    session: AsyncSession = Depends(get_db),
    folder_id: Optional[str] = Query(None, description="仅包含该文件夹内论文；不传表示用户全部已确认论文"),
    max_nodes: int = Query(50, ge=1, le=100, description="最多节点数（论文篇数），≤100"),
):
    if folder_id == "":
        folder_id = None

    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # 查询已确认的论文
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

    # 单一论文特殊处理（无需 LLM）
    if len(papers_for_llm) == 1:
        p = papers_for_llm[0]
        paper, kp = paper_map[p["paper_id"]]
        title = paper.title or ""
        short = title if len(title) <= 24 else title[:21] + "…"
        raw_nodes = [
            {
                "id": paper.id,
                "name": short,
                "type": "paper",
                "category": 0,
                "paperInfo": {
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
            }
        ]
        raw_edges = []
        clusters = [
            {
                "id": "cluster_0",
                "name": "单篇论文",
                "description": "仅有一篇论文，无需聚类",
                "paper_ids": [paper.id],
            }
        ]
        # 合并自定义内容
        final_nodes = await _merge_custom_nodes(session, user["id"], raw_nodes)
        final_edges = await _merge_custom_edges(session, user["id"], raw_edges)
        return success(
            data={
                "nodes": final_nodes,
                "links": final_edges,
                "clusters": clusters,
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

    # 计算论文列表哈希
    paper_ids = [p["paper_id"] for p in papers_for_llm]
    hash_key = _papers_hash(paper_ids)

    # 查询缓存
    cache_q = select(GraphLLMCache).where(
        GraphLLMCache.user_id == user["id"],
        GraphLLMCache.folder_id == folder_id,
        GraphLLMCache.papers_hash == hash_key
    )
    cache = (await session.execute(cache_q)).scalar_one_or_none()

    if cache:
        # 使用缓存
        raw_nodes = cache.nodes
        raw_edges = cache.edges
        clusters = cache.clusters
    else:
        # 调用 LLM 生成
        try:
            llm_result = generate_llm_graph_structure(papers_for_llm)
        except Exception as e:
            return error(
                msg=f"LLM 图结构生成失败: {str(e)}",
                code=500,
                data=None,
                status_code=500,
            )

        # 构建原始节点列表（论文节点）
        raw_nodes = []
        for p in papers_for_llm:
            pid = p["paper_id"]
            paper, kp = paper_map[pid]
            title = paper.title or ""
            short = title if len(title) <= 24 else title[:21] + "…"
            raw_nodes.append({
                "id": pid,
                "name": short,
                "type": "paper",
                "category": 0,  # 临时，稍后根据聚类结果更新
                "paperInfo": {
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
            })

        # 给节点分配聚类 category
        cluster_map: dict[str, int] = {}
        for idx, cluster in enumerate(llm_result.clusters):
            for pid in cluster["paper_ids"]:
                cluster_map[pid] = idx
        for node in raw_nodes:
            node["category"] = cluster_map.get(node["id"], 0)

        # 构建原始边列表
        relation_type_map = {
            "extends": "扩展",
            "applies": "应用",
            "compares": "对比",
            "related": "相关",
        }
        raw_edges = [
            {
                "source": edge["source"],
                "target": edge["target"],
                "relationType": edge["relation_type"],
                "label": f"{relation_type_map.get(edge['relation_type'], '相关')}: {edge['reason']}",
            }
            for edge in llm_result.edges
        ]
        clusters = llm_result.clusters

        # 保存缓存
        new_cache = GraphLLMCache(
            user_id=user["id"],
            folder_id=folder_id,
            papers_hash=hash_key,
            clusters=clusters,
            nodes=raw_nodes,
            edges=raw_edges,
        )
        session.add(new_cache)
        await session.commit()

    # 合并用户自定义节点和边
    final_nodes = await _merge_custom_nodes(session, user["id"], raw_nodes)
    final_edges = await _merge_custom_edges(session, user["id"], raw_edges)

    payload = {
        "nodes": final_nodes,
        "links": final_edges,
        "clusters": clusters,
        "meta": {
            "paper_count": len(papers_for_llm),
            "cluster_count": len(clusters),
            "edge_count": len(final_edges),
            "max_nodes": max_nodes,
            "llm_provider": settings.LLM_PROVIDER,
            "llm_model": settings.DEEPSEEK_MODEL if settings.LLM_PROVIDER == "deepseek" else settings.QWEN_MODEL,
            "cached": cache is not None,
        },
    }

    return success(data=payload, msg="ok", code=0)