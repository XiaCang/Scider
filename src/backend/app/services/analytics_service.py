"""
论文统计分析服务
负责从数据库中提取和聚合论文元数据
"""
import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Paper, Folder
from collections import Counter


class AnalyticsService:
    """统计分析服务类"""
    
    @staticmethod
    async def get_papers_by_folders(
        session: AsyncSession,
        folder_ids: List[str],
        user_id: str
    ) -> List[Paper]:
        """获取指定文件夹下已确认的论文"""
        # 如果 folder_ids 为空，返回该用户所有已确认论文
        if not folder_ids:
            query = (
                select(Paper)
                .where(Paper.user_id == user_id)
                .where(Paper.status == "CONFIRMED")
            )
        else:
            query = (
                select(Paper)
                .where(Paper.folder_id.in_(folder_ids))
                .where(Paper.user_id == user_id)
                .where(Paper.status == "CONFIRMED")
            )
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    def extract_authors(papers: List[Paper]) -> Dict[str, int]:
        """
        提取作者频次统计
        返回: {作者名: 出现次数}
        
        支持格式：
        1. JSON 字符串: '[{"name": "张三"}, {"name": "李四"}]'
        2. 逗号分隔字符串: "张三, 李四, 王五"
        3. 纯文本: "张三"
        """
        author_counter = Counter()
        
        for paper in papers:
            if not paper.authors:
                continue
            
            try:
                # 先尝试解析为 JSON
                authors_data = json.loads(paper.authors)
                
                if isinstance(authors_data, list):
                    for author in authors_data:
                        if isinstance(author, dict):
                            name = author.get("name", "").strip()
                        elif isinstance(author, str):
                            name = author.strip()
                        else:
                            continue
                        
                        if name:
                            author_counter[name] += 1
                elif isinstance(authors_data, str):
                    # JSON 字符串解析后还是字符串，按逗号分割
                    names = [name.strip() for name in authors_data.split(",") if name.strip()]
                    for name in names:
                        author_counter[name] += 1
                    
            except (json.JSONDecodeError, TypeError):
                # 如果不是 JSON 格式，当作逗号分隔的字符串处理
                try:
                    names = [name.strip() for name in paper.authors.split(",") if name.strip()]
                    for name in names:
                        author_counter[name] += 1
                except Exception:
                    # 如果还是失败，整个字符串当作一个作者
                    name = paper.authors.strip()
                    if name:
                        author_counter[name] += 1
        
        return dict(author_counter)
    
    @staticmethod
    def extract_years(papers: List[Paper]) -> Dict[int, int]:
        """
        提取发表年份统计
        返回: {年份: 论文数量}
        """
        year_counter = Counter()
        
        for paper in papers:
            if paper.year:
                year_counter[paper.year] += 1
        
        return dict(year_counter)
    
    @staticmethod
    def extract_venues(papers: List[Paper]) -> Dict[str, int]:
        """
        提取期刊/会议来源统计
        返回: {来源名称: 出现次数}
        """
        venue_counter = Counter()
        
        for paper in papers:
            if paper.source:
                # 标准化处理：去除前后空格
                venue = paper.source.strip()
                if venue:
                    venue_counter[venue] += 1
        
        return dict(venue_counter)
    
    @staticmethod
    def aggregate_all_stats(
        papers: List[Paper]
    ) -> Dict[str, Any]:
        """
        聚合所有维度的统计数据
        """
        return {
            "total_papers": len(papers),
            "authors": AnalyticsService.extract_authors(papers),
            "years": AnalyticsService.extract_years(papers),
            "venues": AnalyticsService.extract_venues(papers),
            # Phase 2 再添加机构和国家的统计
            # "institutions": {},
            # "countries": {}
        }
