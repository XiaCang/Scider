from typing import Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel

from utils.response import success, error
from module.user.service.llm_service import (
    create_provider,
    list_providers,
    get_provider,
    update_provider,
    delete_provider,
)

router = APIRouter()


class LLMProviderIn(BaseModel):
    name: str
    provider: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    enabled: Optional[bool] = True
    user_id: Optional[str] = None


class LLMProviderUpdate(BaseModel):
    """用于 PATCH 的部分更新模型：所有字段均可选以支持部分更新请求。"""
    name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    enabled: Optional[bool] = None
    user_id: Optional[str] = None


@router.get("/api/user/llm-providers")
async def api_list_providers(request: Request):
    """仅返回当前登录用户所拥有的 LLM provider 列表（只包含用户创建的记录）。
    - 需要登录：若未登录返回 401。
    - 仅返回 `provider.user_id == current_user.id` 的记录，不包含全局配置。
    """
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    user_id = user.get("id")

    # 获取全部 provider（crud 的 list_providers 现行为略复杂，直接调用服务再过滤更明确）
    providers = await list_providers(user_id=None)

    # 只保留属于当前用户的 provider
    out = []
    for p in providers:
        if p.user_id != user_id:
            continue
        out.append({
            "id": p.id,
            "name": p.name,
            "provider": p.provider,
            "base_url": p.base_url,
            "default_model": p.default_model,
            "enabled": bool(p.enabled),
            "api_key_masked": (p.api_key[-4:].rjust(len(p.api_key), "*") if p.api_key else None),
            "user_id": p.user_id,
        })

    return success(data=out, msg="查询成功", code=0, status_code=200)


@router.post("/api/user/llm-providers")
async def api_create_provider(request: Request, body: LLMProviderIn):
    """创建 provider：普通用户只能为自己创建，不允许指定他人 user_id。"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    payload = body.dict()
    # 如果请求体带了 user_id，禁止普通用户为他人创建（需 admin）
    if payload.get("user_id") and payload.get("user_id") != user.get("id"):
        return error(msg="无权限为他人创建 provider", code=403, data=None, status_code=403)

    # 默认设置为当前用户
    if not payload.get("user_id"):
        payload["user_id"] = user.get("id")

    provider = await create_provider(payload)
    return success(data={"id": provider.id}, msg="创建成功", code=0, status_code=200)


@router.get("/api/user/llm-providers/{provider_id}")
async def api_get_provider(provider_id: str):
    p = await get_provider(provider_id)
    # 为避免泄露 provider 是否存在（信息泄露），当找不到对应 id 时不返回 404，而是返回与无权限相同的响应。
    if not p:
        return error(msg="无权限", code=403, data=None, status_code=403)
    return success(data={"id": p.id, "name": p.name, "provider": p.provider}, msg="查询成功", code=0, status_code=200)


@router.patch("/api/user/llm-providers/{provider_id}")
async def api_update_provider(request: Request, provider_id: str, body: LLMProviderUpdate):
    """更新 provider：仅允许 owner 修改；全局 provider（user_id is None）暂不允许普通用户修改。"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    p = await get_provider(provider_id)
    if not p:
        return error(msg="无权限", code=403, data=None, status_code=403)

    # 若 provider 为全局配置（user_id is None），禁止修改
    owner_id = p.user_id
    if owner_id is None:
        return error(msg="无权限修改全局 provider", code=403, data=None, status_code=403)

    # 仅 owner 可更新
    if owner_id != user.get("id"):
        return error(msg="无权限修改该 provider", code=403, data=None, status_code=403)

    updates = {k: v for k, v in body.dict().items() if v is not None}
    # 禁止普通用户通过更新接口把 provider 的 user_id 转移给他人
    if updates.get("user_id") and updates.get("user_id") != user.get("id") and (user.get("is_admin") is not True):
        return error(msg="无权限修改 user_id 字段", code=403, data=None, status_code=403)

    p = await update_provider(provider_id, updates)
    if not p:
        return error(msg="更新失败", code=400, data=None, status_code=400)
    return success(data={"id": p.id}, msg="更新成功", code=0, status_code=200)


@router.delete("/api/user/llm-providers/{provider_id}")
async def api_delete_provider(request: Request, provider_id: str):
    """删除 provider：仅 owner 或 admin 可删；全局 provider 需 admin。"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    p = await get_provider(provider_id)
    if not p:
        return error(msg="无权限", code=403, data=None, status_code=403)

    owner_id = p.user_id
    if owner_id is None:
        return error(msg="无权限删除全局 provider", code=403, data=None, status_code=403)

    if owner_id != user.get("id"):
        return error(msg="无权限删除该 provider", code=403, data=None, status_code=403)

    try:
        ok = await delete_provider(provider_id)
    except Exception as e:
        # 记录完整错误到 stderr 以便排查（uvicorn 控制台可见）
        import traceback, sys
        traceback.print_exc()
        print(f"[LLM Delete] exception: {e}", file=sys.stderr)
        return error(msg="删除过程中发生异常，请查看服务日志", code=500, data=None, status_code=500)

    if not ok:
        return error(msg="删除失败或不存在", code=400, data=None, status_code=400)
    return success(data=None, msg="删除成功", code=0, status_code=200)
