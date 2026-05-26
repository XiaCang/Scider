import os
from fastapi import APIRouter, File, UploadFile, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils.response import success, error
from module.user.service.avatar_service import save_user_avatar, delete_user_avatar

router = APIRouter()


@router.post("/api/user/avatar")
async def upload_avatar(request: Request, file: UploadFile = File(...)):
    """
    上传或更新当前登录用户的头像。
    - 接收 multipart/form-data 字段 `file`，仅接受图片（后端简单校验后缀）
    - 返回 avatarUrl
    """
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # 简单后缀校验
    allowed = {".png", ".jpg", ".jpeg", ".webp"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        return error(msg="仅支持图片格式 (.png,.jpg,.jpeg,.webp)", code=400, data=None, status_code=400)

    content = await file.read()
    try:
        res = await save_user_avatar(user["id"], file.filename, content)
    except ValueError as e:
        return error(msg=str(e), code=400, data=None, status_code=400)
    except Exception as e:
        return error(msg="保存头像失败", code=500, data=None, status_code=500)

    return success(data={"avatarUrl": res.get("avatar_url")}, msg="上传成功", code=0, status_code=200)


@router.get("/api/user/avatar")
async def get_avatar(request: Request):
    """返回当前用户的 avatarUrl（若存在）。"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)
    # user state 里可能只有 id/email/name；如需最新 avatar，前端可调用 /api/user/me
    # 这里返回 basic 字段（若你希望读取 DB 可改为查询）
    return success(data={"avatarUrl": user.get("avatar_url")}, msg="查询成功", code=0, status_code=200)


@router.delete("/api/user/avatar")
async def remove_avatar(request: Request):
    """删除当前用户头像（DB 字段与磁盘文件）。"""
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    ok = await delete_user_avatar(user["id"])
    if not ok:
        return error(msg="删除失败或用户不存在", code=400, data=None, status_code=400)
    return success(data=None, msg="删除成功", code=0, status_code=200)
