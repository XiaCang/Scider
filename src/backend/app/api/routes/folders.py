from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.crud_folder import (
    create_folder,
    get_folder_by_id,
    get_folders_by_user,
    update_folder_name,
    delete_folder,
)
from db.session import get_db
from utils.response import success, error

router = APIRouter(prefix="/folders", tags=["folders"])


# ── Request Schemas ──


class CreateFolderIn(BaseModel):
    name: str


class RenameFolderIn(BaseModel):
    name: str


# ── Endpoints ──


@router.post("/")
async def create(
    request: Request,
    payload: CreateFolderIn,
    session: AsyncSession = Depends(get_db),
):
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    if not payload.name or not payload.name.strip():
        return error(msg="文件夹名称不能为空", code=400, data=None, status_code=400)

    folder = await create_folder(
        session=session,
        user_id=user["id"],
        name=payload.name.strip(),
    )
    return success(
        data={
            "id": folder.id,
            "name": folder.name,
            "created_at": folder.created_at.isoformat(),
        },
        msg="创建成功",
        code=0,
        status_code=200,
    )


@router.get("/")
async def list_folders(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    folders = await get_folders_by_user(session=session, user_id=user["id"])
    data = [
        {
            "id": f.id,
            "name": f.name,
            "created_at": f.created_at.isoformat(),
        }
        for f in folders
    ]
    return success(data=data, msg="查询成功", code=0, status_code=200)


@router.get("/{folder_id}")
async def get_folder(
    request: Request,
    folder_id: str,
    session: AsyncSession = Depends(get_db),
):
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    folder = await get_folder_by_id(session=session, folder_id=folder_id)
    if not folder:
        return error(msg="文件夹不存在", code=404, data=None, status_code=404)

    if folder.user_id != user["id"]:
        return error(msg="无权访问该文件夹", code=403, data=None, status_code=403)

    return success(
        data={
            "id": folder.id,
            "name": folder.name,
            "created_at": folder.created_at.isoformat(),
        },
        msg="查询成功",
        code=0,
        status_code=200,
    )


@router.patch("/{folder_id}")
async def rename(
    request: Request,
    folder_id: str,
    payload: RenameFolderIn,
    session: AsyncSession = Depends(get_db),
):
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    if not payload.name or not payload.name.strip():
        return error(msg="文件夹名称不能为空", code=400, data=None, status_code=400)

    folder = await get_folder_by_id(session=session, folder_id=folder_id)
    if not folder:
        return error(msg="文件夹不存在", code=404, data=None, status_code=404)

    if folder.user_id != user["id"]:
        return error(msg="无权修改该文件夹", code=403, data=None, status_code=403)

    updated = await update_folder_name(
        session=session,
        folder_id=folder_id,
        name=payload.name.strip(),
    )
    return success(
        data={
            "id": updated.id,
            "name": updated.name,
            "created_at": updated.created_at.isoformat(),
        },
        msg="修改成功",
        code=0,
        status_code=200,
    )


@router.delete("/{folder_id}")
async def delete(
    request: Request,
    folder_id: str,
    session: AsyncSession = Depends(get_db),
):
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    folder = await get_folder_by_id(session=session, folder_id=folder_id)
    if not folder:
        return error(msg="文件夹不存在", code=404, data=None, status_code=404)

    if folder.user_id != user["id"]:
        return error(msg="无权删除该文件夹", code=403, data=None, status_code=403)

    ok = await delete_folder(session=session, folder_id=folder_id)
    if not ok:
        return error(msg="删除失败", code=500, data=None, status_code=500)

    return success(data=None, msg="删除成功", code=0, status_code=200)
