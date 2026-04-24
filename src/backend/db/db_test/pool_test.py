"""并发连接池测试脚本

用法：
1. 设置 `DATABASE_URL` 与可选环境变量：
   - `DB_POOL_SIZE`（默认 5）
   - `DB_MAX_OVERFLOW`（默认 10）
   - `POOL_TEST_CONCURRENCY`（并发工人数，默认 20）
2. 运行：`python -m src.scripts.pool_test`

脚本会并发创建若干会话并在会话内保持一段时间，期间打印 SQLAlchemy 池的状态，方便观察`checked out`数量是否受限于 `pool_size` 与 `max_overflow`。
"""
import asyncio
import os
import time
import sys

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

# Prefer package-relative import when running as module; fallback inserts src into sys.path
try:
    from ..session import get_async_engine
except Exception:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from backend.db.session import get_async_engine


async def worker(i: int, factory, hold: float = 2.0):
    async with factory() as session:
        print(f"worker {i} acquired session")
        await session.execute(text("SELECT 1"))
        await asyncio.sleep(hold)
    print(f"worker {i} released session")


async def monitor(engine, interval: float = 0.5, duration: float = 5.0):
    end = time.time() + duration
    while time.time() < end:
        try:
            status = engine.sync_engine.pool.status()
        except Exception as e:
            status = f"error reading pool status: {e}"
        print(f"[monitor] pool status: {status}")
        await asyncio.sleep(interval)


async def main():
    concurrency = int(os.getenv("POOL_TEST_CONCURRENCY", "20"))
    hold = float(os.getenv("POOL_TEST_HOLD", "2.0"))

    engine = get_async_engine(echo=False)
    factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    print("Starting pool test with concurrency=", concurrency)
    monitor_task = asyncio.create_task(monitor(engine, interval=0.5, duration=hold + 3))

    tasks = []
    for i in range(concurrency):
        # small stagger to visualize pool behavior
        tasks.append(asyncio.create_task(worker(i, factory, hold)))
        await asyncio.sleep(0.05)

    await asyncio.gather(*tasks)
    await monitor_task
    await engine.dispose()
    print("Pool test completed")


if __name__ == "__main__":
    asyncio.run(main())
