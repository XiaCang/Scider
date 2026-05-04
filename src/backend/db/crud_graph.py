"""图谱：查询用户范围内已生成向量的论文。"""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import KeyPoints, Paper, PaperEmbedding


async def list_papers_with_embeddings(
    session: AsyncSession,
    user_id: str,
    *,
    folder_id: Optional[str] = None,
    max_nodes: int = 200,
) -> list[dict[str, Any]]:
    """
    返回当前用户下已有 embedding 的论文（可选按 folder_id 过滤），按向量更新时间倒序，最多 max_nodes 条。
    每条含 paper 字段、embedding 列表、keypoints 片段（供前端展示）。
    """
    q = (
        select(Paper, PaperEmbedding, KeyPoints)
        .join(PaperEmbedding, PaperEmbedding.paper_id == Paper.id)
        .outerjoin(KeyPoints, KeyPoints.paper_id == Paper.id)
        .where(Paper.user_id == user_id)
    )
    if folder_id:
        q = q.where(Paper.folder_id == folder_id)
    q = q.order_by(PaperEmbedding.updated_at.desc()).limit(max_nodes)

    result = await session.execute(q)
    rows = result.all()

    out: list[dict[str, Any]] = []
    for paper, emb_row, kp in rows:
        vec = emb_row.embedding
        if not isinstance(vec, list) or len(vec) < 2:
            continue
        vec_f = [float(x) for x in vec]
        out.append(
            {
                "paper_id": paper.id,
                "title": paper.title or "",
                "authors": paper.authors or "",
                "year": paper.year if paper.year is not None else 0,
                "status": paper.status.value if paper.status else "",
                "embedding": vec_f,
                "key_points": {
                    "background": (kp.background if kp else "") or "",
                    "method": (kp.methodology if kp else "") or "",
                    "innovation": (kp.innovation if kp else "") or "",
                    "conclusion": (kp.conclusion if kp else "") or "",
                },
            }
        )
    return out
