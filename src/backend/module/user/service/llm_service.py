from typing import Optional, List
from db.session import get_session
from db import crud_llm


async def create_provider(payload: dict):
    """创建 LLM 提供商记录。
    payload 为字典，包含 name, provider, base_url, api_key, default_model, enabled, user_id
    返回创建后的 ORM 对象。
    """
    async with get_session() as session:
        provider = await crud_llm.create_llm_provider(session, **payload)
        return provider


async def list_providers(user_id: Optional[str] = None):
    async with get_session() as session:
        return await crud_llm.list_llm_providers(session, user_id=user_id)


async def get_provider(provider_id: str):
    async with get_session() as session:
        return await crud_llm.get_llm_provider_by_id(session, provider_id)


async def update_provider(provider_id: str, updates: dict):
    async with get_session() as session:
        return await crud_llm.update_llm_provider(session, provider_id, **updates)


async def delete_provider(provider_id: str):
    async with get_session() as session:
        return await crud_llm.delete_llm_provider(session, provider_id)
