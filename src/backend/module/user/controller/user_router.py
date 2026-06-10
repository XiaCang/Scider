from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from module.user.service.auth_service import (
    get_user_by_id,
    update_user_name,
)
from utils.response import success, error


router = APIRouter()


class UpdateNameIn(BaseModel):
    name: str


@router.get("/api/user/me")
async def me(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=400)
    return success(data={"user": user}, msg="查询成功", code=0, status_code=200)


@router.patch("/api/user/me")
async def update_me(payload: UpdateNameIn, request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=400)
    updated = await update_user_name(user["id"], payload.name)
    if not updated:
        return error(msg="User not found", code=404, data=None, status_code=400)
    return success(data={"user": updated}, msg="更新成功", code=0, status_code=200)
