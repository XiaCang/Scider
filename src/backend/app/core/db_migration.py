"""
db_migration.py — 数据库迁移工具函数

提供：
  - run_migration()       以编程方式执行 alembic upgrade head
  - get_migration_info()  查看当前迁移版本和状态
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_ALEMBIC_INI = Path(__file__).resolve().parent.parent / "db" / "alembic.ini"


def _get_alembic_cfg():
    """构造 Alembic Config 对象，自动定位 db/alembic.ini。"""
    from alembic.config import Config

    if not _ALEMBIC_INI.exists():
        raise FileNotFoundError(f"Alembic 配置文件不存在: {_ALEMBIC_INI}")
    cfg = Config(str(_ALEMBIC_INI))
    return cfg


def run_migration() -> dict:
    """
    执行数据库迁移（alembic upgrade head）。

    Returns:
        {"success": True, "revision": "xxx", "message": "..."}
        或
        {"success": False, "message": "错误信息"}
    """
    from alembic import command
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext

    try:
        cfg = _get_alembic_cfg()

        # 迁移前的版本
        old_revision = _get_current_revision()

        old_cwd = Path.cwd()
        os.chdir(str(_ALEMBIC_INI.parent))
        try:
            command.upgrade(cfg, "head")
        finally:
            os.chdir(str(old_cwd))

        new_revision = _get_current_revision()

        if old_revision == new_revision:
            return {
                "success": True,
                "revision": new_revision,
                "message": "数据库已是最新版本，无需迁移",
            }
        return {
            "success": True,
            "revision": new_revision,
            "message": f"迁移完成: {old_revision or '空'} → {new_revision}",
        }
    except Exception as e:
        logger.exception("数据库迁移失败")
        return {"success": False, "message": f"迁移失败: {e}"}


def get_migration_info() -> dict:
    """
    获取当前数据库迁移状态。

    Returns:
        {
            "current_revision": "xxx",
            "is_head": True/False,
            "head_revision": "xxx",
            "pending_migrations": ["..."]
        }
    """
    try:
        current = _get_current_revision()
        head = _get_head_revision()
        pending = _get_pending_migrations()

        return {
            "current_revision": current,
            "head_revision": head,
            "is_head": current == head,
            "pending_migrations": pending,
        }
    except Exception as e:
        return {"error": str(e)}


def _get_current_revision() -> str | None:
    """查询数据库当前所处的迁移版本。"""
    from sqlalchemy import create_engine
    from app.core.config import settings

    sync_url = settings.DATABASE_URL.replace("+asyncmy", "+pymysql").replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_url)
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current = context.get_current_revision()
    engine.dispose()
    return current


def _get_head_revision() -> str | None:
    """查询代码中的最新迁移版本。"""
    from alembic.script import ScriptDirectory

    cfg = _get_alembic_cfg()
    script = ScriptDirectory.from_config(cfg)
    return script.get_current_head()


def _get_pending_migrations() -> list[str]:
    """列出尚未应用的迁移。"""
    from alembic.script import ScriptDirectory

    cfg = _get_alembic_cfg()
    script = ScriptDirectory.from_config(cfg)

    current = _get_current_revision()
    if current is None:
        return [s.revision for s in script.walk_revisions("base", "head")]

    head = script.get_current_head()
    if current == head:
        return []

    pending = []
    for s in script.walk_revisions(current, head):
        pending.append(s.revision)
    return pending
