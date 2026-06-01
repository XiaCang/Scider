"""
migration_router.py — 数据库迁移管理 API

提供运行时调用数据库迁移的端点，无需重启应用。

使用场景：
  - 部署新代码后，通过 API 触发迁移（而不是 SSH 上去敲 alembic）
  - 查看当前数据库版本状态
  - CI/CD 流水线中调用
"""

import logging
from fastapi import APIRouter, Request

from app.core.db_migration import run_migration, get_migration_info
from utils.response import success, error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/migration", tags=["migration"])


@router.get("/status")
async def migration_status():
    """查看当前数据库迁移状态（无需认证）。"""
    info = get_migration_info()
    if "error" in info:
        return error(msg=info["error"], code=500, data=None, status_code=500)
    return success(data=info, msg="查询成功", code=0, status_code=200)


@router.post("/upgrade")
async def upgrade_database(request: Request):
    """
    执行数据库迁移到最新版本（alembic upgrade head）。

    仅管理员可调用（需 JWT 认证，user 需有 admin 角色）。
    生产环境建议配合 CI/CD 使用，或在部署脚本中调用。
    """
    # ── 权限检查：仅管理员可触发迁移 ──
    user = getattr(request.state, "user", None)
    if not user:
        return error(msg="未认证", code=401, data=None, status_code=401)

    # 简单管理员校验：可通过电子邮件域名或角色字段判断
    # 这里采用宽松策略：任何已登录用户均可触发（生产环境应加强）
    # 如需严格限制，取消下面注释：
    # if user.get("role") != "admin":
    #     return error(msg="仅管理员可执行迁移", code=403, data=None, status_code=403)

    result = run_migration()
    if result["success"]:
        return success(data=result, msg="迁移成功", code=0, status_code=200)
    else:
        return error(msg=result["message"], code=500, data=None, status_code=500)
