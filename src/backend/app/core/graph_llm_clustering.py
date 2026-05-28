"""
LLM-based Graph Structure Generation and Clustering.

基于 LLM 分析论文四要素，生成主题聚类和语义关系边。
"""

import json
import logging
import re
from typing import Any

from app.core.llm_client import chat_completion
from app.core.graph_llm_prompts import (
    GRAPH_CLUSTERING_SYSTEM_PROMPT,
    build_graph_clustering_user_prompt,
)

logger = logging.getLogger(__name__)


class GraphClusteringResult:
    """LLM 图聚类结果"""

    def __init__(self, clusters: list[dict], edges: list[dict]):
        self.clusters = clusters
        self.edges = edges

    def to_dict(self) -> dict[str, Any]:
        return {
            "clusters": self.clusters,
            "edges": self.edges,
        }


def _parse_llm_response(raw: str) -> dict:
    """
    从 LLM 原始回复中提取聚类和边的 JSON。

    兼容模型将 JSON 包在 ```json … ``` 代码块内的情况。
    """
    text = raw.strip()

    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"LLM 返回的 JSON 解析失败: {e}\n原始回复: {raw[:500]}")
        raise ValueError(f"LLM 返回格式错误: {e}")

    if "clusters" not in data or "edges" not in data:
        raise ValueError("LLM 返回缺少 clusters 或 edges 字段")

    return data


def _validate_and_clean_result(
    data: dict,
    paper_ids: set[str],
) -> GraphClusteringResult:
    """
    验证并清洗 LLM 返回的聚类结果。

    - 确保所有 paper_id 都在输入列表中
    - 确保每篇论文只属于一个簇
    - 过滤无效的边
    """
    clusters = data.get("clusters", [])
    edges = data.get("edges", [])

    assigned_papers: set[str] = set()
    valid_clusters: list[dict] = []

    for cluster in clusters:
        cluster_id = cluster.get("id", "")
        cluster_name = cluster.get("name", "未命名主题")
        cluster_desc = cluster.get("description", "")
        cluster_papers = cluster.get("paper_ids", [])

        valid_papers = [
            pid for pid in cluster_papers
            if pid in paper_ids and pid not in assigned_papers
        ]

        if not valid_papers:
            continue

        assigned_papers.update(valid_papers)

        valid_clusters.append({
            "id": cluster_id or f"cluster_{len(valid_clusters)}",
            "name": cluster_name[:50],
            "description": cluster_desc[:200],
            "paper_ids": valid_papers,
        })

    unassigned = paper_ids - assigned_papers
    if unassigned:
        logger.warning(f"有 {len(unassigned)} 篇论文未被分配到任何簇，自动归入默认簇")
        valid_clusters.append({
            "id": f"cluster_{len(valid_clusters)}",
            "name": "其他",
            "description": "未分类的论文",
            "paper_ids": list(unassigned),
        })

    valid_edges: list[dict] = []
    for edge in edges:
        source = edge.get("source", "")
        target = edge.get("target", "")
        relation_type = edge.get("relation_type", "related")
        reason = edge.get("reason", "")

        if source not in paper_ids or target not in paper_ids:
            continue
        if source == target:
            continue

        valid_edges.append({
            "source": source,
            "target": target,
            "relation_type": relation_type,
            "reason": reason[:100],
        })

    return GraphClusteringResult(clusters=valid_clusters, edges=valid_edges)


def generate_llm_graph_structure(
    papers: list[dict[str, Any]],
    *,
    timeout: int = 120,
) -> GraphClusteringResult:
    """
    调用 LLM 生成论文图谱的聚类和语义关系边。

    Args:
        papers: 论文列表，每篇包含 paper_id, title, authors, year, key_points
        timeout: LLM 调用超时时间（秒）

    Returns:
        GraphClusteringResult 对象，包含聚类和边信息

    Raises:
        ValueError: LLM 返回格式错误或解析失败
        RuntimeError: LLM 调用失败
    """
    if not papers:
        return GraphClusteringResult(clusters=[], edges=[])

    if len(papers) == 1:
        single_paper = papers[0]
        return GraphClusteringResult(
            clusters=[{
                "id": "cluster_0",
                "name": "单篇论文",
                "description": "仅有一篇论文，无需聚类",
                "paper_ids": [single_paper["paper_id"]],
            }],
            edges=[],
        )

    paper_ids = {p["paper_id"] for p in papers}

    user_prompt = build_graph_clustering_user_prompt(papers)

    logger.info(f"开始调用 LLM 生成图结构，论文数量: {len(papers)}")

    try:
        raw_response = chat_completion(
            GRAPH_CLUSTERING_SYSTEM_PROMPT,
            user_prompt,
        )
        logger.debug(f"LLM 原始回复 (前 300 字): {raw_response[:300]}")
    except Exception as e:
        logger.exception("LLM 调用失败")
        raise RuntimeError(f"LLM 调用失败: {e}")

    try:
        data = _parse_llm_response(raw_response)
        result = _validate_and_clean_result(data, paper_ids)
        logger.info(
            f"LLM 图结构生成成功: {len(result.clusters)} 个簇, {len(result.edges)} 条边"
        )
        return result
    except ValueError as e:
        logger.exception("LLM 返回解析失败")
        raise
