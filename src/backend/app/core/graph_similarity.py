"""基于向量余弦相似度构建边（无第三方数值库依赖）。"""

from __future__ import annotations


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na**0.5 * nb**0.5)


def build_similarity_edges(
    paper_ids: list[str],
    embeddings: list[list[float]],
    *,
    min_similarity: float,
    top_k_per_node: int,
    max_edges: int = 1500,
) -> list[tuple[str, str, float]]:
    """
    无向边：每个节点保留与其它节点余弦相似度最高且 >= min_similarity 的 top_k 条，
    去重后按相似度截断到 max_edges。
    """
    n = len(paper_ids)
    if n < 2:
        return []

    edges: list[tuple[str, str, float]] = []
    seen: set[tuple[str, str]] = set()

    for i in range(n):
        scores: list[tuple[int, float]] = []
        for j in range(n):
            if i == j:
                continue
            s = cosine_similarity(embeddings[i], embeddings[j])
            if s >= min_similarity:
                scores.append((j, s))
        scores.sort(key=lambda t: -t[1])
        for j, s in scores[:top_k_per_node]:
            a, b = paper_ids[i], paper_ids[j]
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)
            edges.append((a, b, s))

    edges.sort(key=lambda t: -t[2])
    return edges[:max_edges]
