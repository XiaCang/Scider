"""图谱编辑：自定义节点和边的 CRUD 操作"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import GraphNode, GraphEdge
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
    """更新节点属性"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    q = select(GraphNode).where(GraphNode.id == node_id, GraphNode.user_id == user["id"])
    result = await session.execute(q)
    node = result.scalar_one_or_none()

    if not node:
        return error(msg="节点不存在", code=404, data=None, status_code=404)

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
    """删除节点，自动级联删除关联的所有边"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    q = select(GraphNode).where(GraphNode.id == node_id, GraphNode.user_id == user["id"])
    result = await session.execute(q)
    node = result.scalar_one_or_none()

    if not node:
        return error(msg="节点不存在", code=404, data=None, status_code=404)

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


@router.post("/edges", response_model=None)
async def create_edge(
    payload: EdgeCreateIn,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """创建节点间的关系边"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    source_q = select(GraphNode).where(GraphNode.id == payload.source_id, GraphNode.user_id == user["id"])
    source_result = await session.execute(source_q)
    if not source_result.scalar_one_or_none():
        return error(msg="源节点不存在", code=404, data=None, status_code=404)

    target_q = select(GraphNode).where(GraphNode.id == payload.target_id, GraphNode.user_id == user["id"])
    target_result = await session.execute(target_q)
    if not target_result.scalar_one_or_none():
        return error(msg="目标节点不存在", code=404, data=None, status_code=404)

    edge = GraphEdge(
        user_id=user["id"],
        source_id=payload.source_id,
        target_id=payload.target_id,
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
    """更新边的属性"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    q = select(GraphEdge).where(GraphEdge.id == edge_id, GraphEdge.user_id == user["id"])
    result = await session.execute(q)
    edge = result.scalar_one_or_none()

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
    """删除边"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    q = select(GraphEdge).where(GraphEdge.id == edge_id, GraphEdge.user_id == user["id"])
    result = await session.execute(q)
    edge = result.scalar_one_or_none()

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
