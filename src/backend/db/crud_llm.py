from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from .models import LLMProvider


async def create_llm_provider(session: AsyncSession, **kwargs) -> LLMProvider:
    """创建一个新的 LLM 提供商记录并返回该对象。"""
    # 如果创建的是用户级别的 provider 且启用，则需要将该用户其他 provider 置为 disabled
    user_id = kwargs.get("user_id")
    enabled = kwargs.get("enabled")
    if user_id and enabled:
        q = update(LLMProvider).where(LLMProvider.user_id == user_id).values(enabled=False).execution_options(synchronize_session="fetch")
        await session.execute(q)

    provider = LLMProvider(**kwargs)
    session.add(provider)
    await session.commit()
    await session.refresh(provider)
    return provider


async def get_llm_provider_by_id(session: AsyncSession, provider_id: str) -> Optional[LLMProvider]:
    q = select(LLMProvider).where(LLMProvider.id == provider_id)
    res = await session.execute(q)
    return res.scalars().first()


async def list_llm_providers(session: AsyncSession, user_id: Optional[str] = None) -> List[LLMProvider]:
    """列出 LLM 提供商。若提供 user_id，则返回全局 + 该用户的私有配置。
    否则返回全部（谨慎暴露给前端）。"""
    q = select(LLMProvider)
    if user_id is not None:
        # 返回全局配置（user_id IS NULL）与该用户的配置
        q = select(LLMProvider).where((LLMProvider.user_id == None) | (LLMProvider.user_id == user_id))
    res = await session.execute(q)
    return list(res.scalars().all())


async def update_llm_provider(session: AsyncSession, provider_id: str, **updates) -> Optional[LLMProvider]:
    # 若更新把 enabled 设为 True，则需保证同一用户的其他 provider 设为 False
    if updates.get("enabled") is True:
        # 先找出当前 provider 的 owner
        existing = await get_llm_provider_by_id(session, provider_id)
        owner = existing.user_id if existing else None
        if owner:
            q0 = update(LLMProvider).where(LLMProvider.user_id == owner, LLMProvider.id != provider_id).values(enabled=False).execution_options(synchronize_session="fetch")
            await session.execute(q0)

    q = update(LLMProvider).where(LLMProvider.id == provider_id).values(**updates).execution_options(synchronize_session="fetch")
    await session.execute(q)
    await session.commit()
    return await get_llm_provider_by_id(session, provider_id)


async def delete_llm_provider(session: AsyncSession, provider_id: str) -> bool:
    q = delete(LLMProvider).where(LLMProvider.id == provider_id)
    res = await session.execute(q)
    await session.commit()
    return res.rowcount > 0
