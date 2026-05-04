"""
测试PDF上传和解析流程
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from db.session import get_session
from db.models import Paper, PaperStatus
from sqlalchemy import select


async def test_upload_flow():
    """测试上传后的论文状态"""
    async with get_session() as session:
        # 查询最新的论文
        result = await session.execute(
            select(Paper).order_by(Paper.created_at.desc()).limit(1)
        )
        paper = result.scalar_one_or_none()
        
        if not paper:
            print("❌ 数据库中没有论文")
            return
        
        print("\n" + "="*80)
        print("最新论文信息:")
        print("="*80)
        print(f"ID: {paper.id}")
        print(f"标题: {paper.title}")
        print(f"状态: {paper.status.value}")
        print(f"创建时间: {paper.created_at}")
        print(f"MD5: {paper.md5_hash}")
        print(f"文件大小: {paper.file_size} bytes")
        print("="*80)
        
        # 检查状态是否正确
        if paper.status == PaperStatus.PENDING_PARSING:
            print("\n✅ 论文已创建，状态为 PENDING_PARSING（等待解析）")
            print("💡 Celery Worker应该正在处理此任务...")
        elif paper.status == PaperStatus.PARSING:
            print("\n✅ 论文正在解析中 (PARSING)")
        elif paper.status == PaperStatus.PENDING_EXTRACTION:
            print("\n✅ PDF解析完成，等待LLM提取关键点 (PENDING_EXTRACTION)")
        elif paper.status == PaperStatus.PENDING_CONFIRMATION:
            print("\n✅ LLM提取完成，等待用户确认 (PENDING_CONFIRMATION)")
        elif paper.status == PaperStatus.FAILED:
            print("\n❌ 论文解析失败 (FAILED)")
        else:
            print(f"\n⚠️ 未知状态: {paper.status.value}")
        
        print("\n提示:")
        print("1. 前端应该在上传后立即显示此论文（状态为'解析中'）")
        print("2. 解析完成后，状态会自动更新为'待确认'")
        print("3. ParsingProgressPopover应在完成后自动移除任务")
        print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_upload_flow())
