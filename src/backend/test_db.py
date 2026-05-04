"""快速测试增删改查，在 src/backend 目录下运行：python test_db.py"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from db.session import get_session
from db.models import User
from sqlalchemy import select


async def main():
    # 增
    async with get_session() as s:
        user = User(email="test@scider.com", password="hashed_pw", name="测试用户")
        s.add(user)
        await s.commit()
        await s.refresh(user)
        print(f"创建用户: id={user.id}, email={user.email}")
        user_id = user.id

    # 查
    async with get_session() as s:
        result = await s.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        print(f"查询用户: name={user.name}")

    # 改
    async with get_session() as s:
        result = await s.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        user.name = "改名后"
        await s.commit()
        print(f"更新用户: name={user.name}")

    # 删
    async with get_session() as s:
        result = await s.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        await s.delete(user)
        await s.commit()
        print("删除用户成功")


asyncio.run(main())