"""图谱编辑：自定义节点和边的 CRUD 操作，支持系统节点/边的覆盖与删除。"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import GraphNode, GraphEdge, Paper
from db.session import get_db
from utils.response import error, success

router = APIRouter(prefix="/graph/edit", tags=["graph-edit"])


class NodeCreateIn(BaseModel):
    paper_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    node_type: str = Field(default="custom", max_length=50)
    category: int = Field(default=0, ge=0)
    properties: Optional[dict[str, Any]] = None


class NodeUpdateIn(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    node_type: Optional[str] = Field(None, max_length=50)
    category: Optional[int] = Field(None, ge=0)
    properties: Optional[dict[str, Any]] = None


class EdgeCreateIn(BaseModel):
    source_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    relation_type: str = Field(default="related", max_length=50)
    label: Optional[str] = Field(None, max_length=255)
    properties: Optional[dict[str, Any]] = None


class EdgeUpdateIn(BaseModel):
    relation_type: Optional[str] = Field(None, max_length=50)
    label: Optional[str] = Field(None, max_length=255)
    properties: Optional[dict[str, Any]] = None


# ---------- 辅助函数 ----------
async def _get_or_create_node(
    session: AsyncSession,
    user_id: str,
    node_id: str,
    default_name: Optional[str] = None,
    default_type: str = "paper",
    default_category: int = 0,
) -> Optional[GraphNode]:
    # 1. 按 id 直接查找
    node = await session.get(GraphNode, node_id)
    if node and node.user_id == user_id:
        return node

    # 2. 按 paper_id 查找
    q_paper = (
        select(GraphNode)
        .where(GraphNode.paper_id == node_id, GraphNode.user_id == user_id)
        .order_by(GraphNode.updated_at.desc())
    )
    result = await session.execute(q_paper)
    nodes = result.scalars().all()
    if nodes:
        target = nodes[0]  # 最新的一个
        # 如果查到的节点 id 等于传入的 node_id，直接返回
        if target.id == node_id:
            # 删除多余的重复记录（如果有）
            for extra in nodes[1:]:
                await session.delete(extra)
            await session.commit()
            return target
        else:
            # 查到的节点 id 不是我们想要的（例如是自定义的 UUID），但 paper_id 匹配
            # 需要创建一个新节点，id = node_id，复制原节点的属性，然后删除原节点
            # 检查 node_id 是否已被其他节点占用（不应该，因为第一步已查过）
            existing = await session.get(GraphNode, node_id)
            if existing:
                # 如果该 id 已被占用（例如另一个自定义节点），则无法创建，返回原有节点
                # 这种情况下，前端需要传递正确的节点 id，暂时返回 target
                return target
            # 创建新节点
            new_node = GraphNode(
                id=node_id,
                user_id=user_id,
                paper_id=target.paper_id,
                name=target.name,
                node_type=target.node_type,
                category=target.category,
                properties=target.properties,
            )
            session.add(new_node)
            # 删除旧节点（级联删除其关联的边，但需要先迁移边）
            # 将旧节点关联的边的 source_id/target_id 更新为新节点 id
            await session.execute(
                update(GraphEdge).where(GraphEdge.source_id == target.id).values(source_id=node_id)
            )
            await session.execute(
                update(GraphEdge).where(GraphEdge.target_id == target.id).values(target_id=node_id)
            )
            await session.delete(target)
            await session.commit()
            return new_node

    # 3. 检查 node_id 是否是一个真实论文，若是则创建节点
    paper = await session.get(Paper, node_id)
    if paper and paper.user_id == user_id:
        new_node = GraphNode(
            id=node_id,
            user_id=user_id,
            paper_id=paper.id,
            name=default_name or paper.title or "",
            node_type=default_type,
            category=default_category,
        )
        session.add(new_node)
        await session.commit()
        return new_node

    return None


async def _get_or_create_edge(
    session: AsyncSession,
    user_id: str,
    source_id: str,
    target_id: str,
    relation_type: str,
    default_label: Optional[str] = None,
) -> Optional[GraphEdge]:
    """
    根据 (source_id, target_id, relation_type) 获取或创建 GraphEdge。
    如果不存在则创建一条覆盖记录（用于编辑系统边）。
    """
    q = select(GraphEdge).where(
        GraphEdge.user_id == user_id,
        GraphEdge.source_id == source_id,
        GraphEdge.target_id == target_id,
        GraphEdge.relation_type == relation_type,
    )
    edge = (await session.execute(q)).scalar_one_or_none()
    if edge:
        return edge

    # 确保源和目标节点存在（可能是论文 ID，自动创建）
    source_node = await _get_or_create_node(session, user_id, source_id)
    target_node = await _get_or_create_node(session, user_id, target_id)
    if not source_node or not target_node:
        return None

    # 创建新边
    new_edge = GraphEdge(
        user_id=user_id,
        source_id=source_id,
        target_id=target_id,
        relation_type=relation_type,
        label=default_label,
    )
    session.add(new_edge)
    await session.flush()
    return new_edge


# ---------- 节点 CRUD ----------
@router.post("/nodes", response_model=None)
async def create_node(
    payload: NodeCreateIn,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """创建自定义图谱节点"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    node = GraphNode(
        user_id=user["id"],
        paper_id=payload.paper_id,
        name=payload.name,
        node_type=payload.node_type,
        category=payload.category,
        properties=payload.properties,
    )
    session.add(node)
    await session.commit()
    await session.refresh(node)

    return success(
        data={
            "id": node.id,
            "name": node.name,
            "node_type": node.node_type,
            "category": node.category,
            "paper_id": node.paper_id,
            "properties": node.properties,
        },
        msg="节点创建成功",
        code=0,
    )


@router.get("/nodes", response_model=None)
async def list_nodes(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有自定义图谱节点"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    q = select(GraphNode).where(GraphNode.user_id == user["id"]).order_by(GraphNode.created_at.desc())
    result = await session.execute(q)
    nodes = result.scalars().all()

    return success(
        data={
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "node_type": n.node_type,
                    "category": n.category,
                    "paper_id": n.paper_id,
                    "properties": n.properties,
                }
                for n in nodes
            ],
            "total": len(nodes),
        },
        msg="ok",
        code=0,
    )


@router.patch("/nodes/{node_id}", response_model=None)
async def update_node(
    node_id: str,
    payload: NodeUpdateIn,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """
    更新节点属性。
    注意：禁止更新系统论文节点以及任何关联 paper_id 的节点（即覆盖节点），
    只允许更新纯自定义节点（paper_id 为 NULL 且 id 不是论文 ID）。
    """
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # 1. 查找自定义节点
    q = select(GraphNode).where(GraphNode.id == node_id, GraphNode.user_id == user["id"])
    node = (await session.execute(q)).scalar_one_or_none()

    # 2. 如果没有找到，检查 node_id 是否是一个真实论文 ID（系统节点）
    if not node:
        paper = await session.get(Paper, node_id)
        if paper and paper.user_id == user["id"]:
            # 禁止更新系统论文节点
            return error(msg="系统论文节点不可编辑", code=403, data=None, status_code=403)
        else:
            return error(msg="节点不存在", code=404, data=None, status_code=404)

    # 3. 如果该节点关联了 paper_id（即覆盖节点），也不允许编辑
    if node.paper_id is not None:
        return error(msg="无法编辑关联论文的节点，请创建自定义节点", code=403, data=None, status_code=403)

    # 4. 更新纯自定义节点（paper_id 为 NULL）
    if payload.name is not None:
        node.name = payload.name
    if payload.node_type is not None:
        node.node_type = payload.node_type
    if payload.category is not None:
        node.category = payload.category
    if payload.properties is not None:
        node.properties = payload.properties

    await session.commit()
    await session.refresh(node)

    return success(
        data={
            "id": node.id,
            "name": node.name,
            "node_type": node.node_type,
            "category": node.category,
            "paper_id": node.paper_id,
            "properties": node.properties,
        },
        msg="节点更新成功",
        code=0,
    )


@router.delete("/nodes/{node_id}", response_model=None)
async def delete_node(
    node_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """删除节点，自动级联删除关联的所有边。支持删除系统论文节点（删除覆盖记录，恢复默认）。"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # 查找节点
    q = select(GraphNode).where(GraphNode.id == node_id, GraphNode.user_id == user["id"])
    node = (await session.execute(q)).scalar_one_or_none()
    if not node:
        # 可能 node_id 是论文 ID 但用户未创建覆盖记录，此时返回成功（无记录可删）
        paper = await session.get(Paper, node_id)
        if paper and paper.user_id == user["id"]:
            # 没有覆盖节点，视为删除成功（无需操作）
            return success(
                data={"deleted_node_id": node_id, "deleted_edges_count": 0},
                msg="节点无自定义记录，已忽略",
                code=0,
            )
        return error(msg="节点不存在", code=404, data=None, status_code=404)

    # 删除关联边
    deleted_edges = await session.execute(
        delete(GraphEdge).where(
            (GraphEdge.source_id == node_id) | (GraphEdge.target_id == node_id)
        )
    )
    await session.delete(node)
    await session.commit()

    return success(
        data={
            "deleted_node_id": node_id,
            "deleted_edges_count": deleted_edges.rowcount,
        },
        msg=f"节点已删除，同时删除了 {deleted_edges.rowcount} 条关联的边",
        code=0,
    )


# ---------- 边 CRUD ----------
@router.post("/edges", response_model=None)
async def create_edge(
    payload: EdgeCreateIn,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # 获取或创建节点，得到数据库中的实际 id
    source_node = await _get_or_create_node(session, user["id"], payload.source_id)
    target_node = await _get_or_create_node(session, user["id"], payload.target_id)
    if not source_node or not target_node:
        return error(msg="源节点或目标节点不存在", code=404, data=None, status_code=404)

    edge = GraphEdge(
        user_id=user["id"],
        source_id=source_node.id,   # 使用实际节点的 id
        target_id=target_node.id,
        relation_type=payload.relation_type,
        label=payload.label,
        properties=payload.properties,
    )
    session.add(edge)
    await session.commit()
    await session.refresh(edge)

    return success(
        data={
            "id": edge.id,
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "relation_type": edge.relation_type,
            "label": edge.label,
            "properties": edge.properties,
        },
        msg="边创建成功",
        code=0,
    )

@router.get("/edges", response_model=None)
async def list_edges(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有自定义图谱边"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    q = select(GraphEdge).where(GraphEdge.user_id == user["id"]).order_by(GraphEdge.created_at.desc())
    result = await session.execute(q)
    edges = result.scalars().all()

    return success(
        data={
            "edges": [
                {
                    "id": e.id,
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "relation_type": e.relation_type,
                    "label": e.label,
                    "properties": e.properties,
                }
                for e in edges
            ],
            "total": len(edges),
        },
        msg="ok",
        code=0,
    )


@router.patch("/edges/{edge_id}", response_model=None)
async def update_edge(
    edge_id: str,
    payload: EdgeUpdateIn,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """
    更新边的属性。
    支持系统边：edge_id 格式为 `edge_{source}_{target}_{relation_type}`，后端会解析并创建覆盖记录。
    """
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # 尝试解析 edge_id 格式
    source_id = None
    target_id = None
    relation_type = None
    if edge_id.startswith("edge_"):
        parts = edge_id.split("_", 3)  # ["edge", source, target, relation_type]
        if len(parts) == 4:
            source_id = parts[1]
            target_id = parts[2]
            relation_type = parts[3]

    if source_id and target_id and relation_type:
        # 系统边：按三元组查找或创建覆盖记录
        edge = await _get_or_create_edge(
            session,
            user["id"],
            source_id,
            target_id,
            relation_type,
            default_label="",
        )
        if not edge:
            return error(msg="边不存在", code=404, data=None, status_code=404)
    else:
        # 普通自定义边：按 id 查找
        q = select(GraphEdge).where(GraphEdge.id == edge_id, GraphEdge.user_id == user["id"])
        edge = (await session.execute(q)).scalar_one_or_none()
        if not edge:
            return error(msg="边不存在", code=404, data=None, status_code=404)

    if payload.relation_type is not None:
        edge.relation_type = payload.relation_type
    if payload.label is not None:
        edge.label = payload.label
    if payload.properties is not None:
        edge.properties = payload.properties

    await session.commit()
    await session.refresh(edge)

    return success(
        data={
            "id": edge.id,
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "relation_type": edge.relation_type,
            "label": edge.label,
            "properties": edge.properties,
        },
        msg="边更新成功",
        code=0,
    )


@router.delete("/edges/{edge_id}", response_model=None)
async def delete_edge(
    edge_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """
    删除边。支持系统边：edge_id 格式为 `edge_{source}_{target}_{relation_type}`，
    会删除对应的覆盖记录（若存在）。
    """
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # 解析 edge_id
    source_id = None
    target_id = None
    relation_type = None
    if edge_id.startswith("edge_"):
        parts = edge_id.split("_", 3)
        if len(parts) == 4:
            source_id = parts[1]
            target_id = parts[2]
            relation_type = parts[3]

    if source_id and target_id and relation_type:
        # 删除覆盖记录
        q = select(GraphEdge).where(
            GraphEdge.user_id == user["id"],
            GraphEdge.source_id == source_id,
            GraphEdge.target_id == target_id,
            GraphEdge.relation_type == relation_type,
        )
        edge = (await session.execute(q)).scalar_one_or_none()
        if edge:
            await session.delete(edge)
            await session.commit()
            return success(
                data={"deleted_edge_id": edge_id},
                msg="边覆盖记录已删除",
                code=0,
            )
        else:
            # 没有覆盖记录，视为删除成功（系统边默认不可见）
            return success(
                data={"deleted_edge_id": edge_id},
                msg="边无自定义记录，已忽略",
                code=0,
            )
    else:
        # 普通自定义边
        q = select(GraphEdge).where(GraphEdge.id == edge_id, GraphEdge.user_id == user["id"])
        edge = (await session.execute(q)).scalar_one_or_none()
        if not edge:
            return error(msg="边不存在", code=404, data=None, status_code=404)
        await session.delete(edge)
        await session.commit()
        return success(
            data={"deleted_edge_id": edge_id},
            msg="边已删除",
            code=0,
        )


@router.get("/graph", response_model=None)
async def get_custom_graph(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """获取当前用户的完整自定义图谱"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    nodes_q = select(GraphNode).where(GraphNode.user_id == user["id"])
    nodes_result = await session.execute(nodes_q)
    nodes = nodes_result.scalars().all()

    edges_q = select(GraphEdge).where(GraphEdge.user_id == user["id"])
    edges_result = await session.execute(edges_q)
    edges = edges_result.scalars().all()

    return success(
        data={
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type,
                    "category": n.category,
                    "paperInfo": {"id": n.paper_id, "properties": n.properties} if n.paper_id else {"properties": n.properties},
                }
                for n in nodes
            ],
            "links": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "relationType": e.relation_type,
                    "label": e.label,
                    "properties": e.properties,
                }
                for e in edges
            ],
            "meta": {
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        },
        msg="ok",
        code=0,
    )