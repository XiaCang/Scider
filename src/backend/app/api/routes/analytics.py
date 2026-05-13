"""
统计分析 API 路由
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel

from db.session import get_db
from app.services.analytics_service import AnalyticsService
from utils.response import success, error

router = APIRouter(prefix="/analytics", tags=["analytics"])


class AggregateRequest(BaseModel):
    """聚合请求体"""
    folder_ids: List[str] = []  # 空列表表示分析所有论文


@router.post("/aggregate")
async def aggregate_analytics(
    request: Request,
    payload: AggregateRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    聚合选中文件夹的论文统计数据
    
    - **folder_ids**: 选中的文件夹ID列表，空列表表示分析全部
    """
    # 从 JWT 中获取用户
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="未认证")
    
    user_id = user["id"]
    
    try:
        # 1. 获取论文列表
        papers = await AnalyticsService.get_papers_by_folders(
            session=session,
            folder_ids=payload.folder_ids,
            user_id=user_id
        )
        
        if not papers:
            return success(
                data={
                    "total_papers": 0,
                    "authors": {},
                    "years": {},
                    "venues": {},
                    "message": "未找到已确认的论文"
                },
                msg="暂无可分析的论文"
            )
        
        # 2. 聚合统计数据
        stats = AnalyticsService.aggregate_all_stats(papers)
        
        return success(data=stats, msg="分析完成")
        
    except Exception as e:
        return error(msg=f"分析失败: {str(e)}", code=500)


@router.get("/stats/{dimension}")
async def get_dimension_stats(
    dimension: str,
    request: Request,
    folder_ids: str = "",  # JSON 字符串格式的文件夹ID列表
    session: AsyncSession = Depends(get_db)
):
    """
    获取特定维度的统计数据
    
    - **dimension**: 统计维度 (author/year/venue)
    - **folder_ids**: 文件夹ID列表的JSON字符串
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="未认证")
    
    user_id = user["id"]
    
    # 解析 folder_ids
    import json
    try:
        folder_id_list = json.loads(folder_ids) if folder_ids else []
    except json.JSONDecodeError:
        folder_id_list = []
    
    try:
        # 获取论文
        papers = await AnalyticsService.get_papers_by_folders(
            session=session,
            folder_ids=folder_id_list,
            user_id=user_id
        )
        
        # 根据维度返回对应统计
        if dimension == "author":
            data = AnalyticsService.extract_authors(papers)
        elif dimension == "year":
            data = AnalyticsService.extract_years(papers)
        elif dimension == "venue":
            data = AnalyticsService.extract_venues(papers)
        else:
            return error(msg=f"不支持的维度: {dimension}", code=400)
        
        return success(data=data)
        
    except Exception as e:
        return error(msg=f"查询失败: {str(e)}", code=500)