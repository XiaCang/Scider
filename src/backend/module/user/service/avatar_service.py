import os
import hashlib
import aiofiles
from app.core.config import settings
from db.session import get_session
from db.crud_user import get_user


async def _ensure_avatar_dir():
    """确保 avatars 存储目录存在。"""
    avatar_dir = os.path.join(settings.UPLOAD_DIR, "avatars")
    os.makedirs(avatar_dir, exist_ok=True)
    return avatar_dir


async def save_user_avatar(user_id: str, filename: str, content: bytes):
    """
    保存用户头像：
    - 计算文件 md5 并以 md5+后缀命名，防止文件名冲突
    - 将文件写入 UPLOAD_DIR/avatars
    - 更新 User.avatar_path 与 avatar_url（相对 /uploads 挂载）
    返回 updated user dict 或抛出异常。
    """
    avatar_dir = await _ensure_avatar_dir()
    ext = os.path.splitext(filename)[1].lower() if filename else ".png"
    md5 = hashlib.md5(content).hexdigest()
    storage_name = f"{md5}{user_id}{ext}"
    storage_path = os.path.join(avatar_dir, storage_name)

    # 异步写文件
    async with aiofiles.open(storage_path, "wb") as f:
        await f.write(content)

    # 更新数据库记录
    async with get_session() as session:
        user = await get_user(session, user_id)
        if not user:
            # 写入了文件但找不到用户：删除文件并抛错
            try:
                os.remove(storage_path)
            except Exception:
                pass
            raise ValueError("user not found")

        # 删除旧头像文件（如果存在且不同于新文件）
        old_path = user.avatar_path
        if old_path and os.path.exists(old_path) and os.path.abspath(old_path) != os.path.abspath(storage_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

        user.avatar_path = storage_path
        # avatar_url 对前端可见，挂载点为 /uploads/avatars/<file>
        user.avatar_url = f"/uploads/avatars/{storage_name}"

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return {"id": user.id, "email": user.email, "name": user.name, "avatar_url": user.avatar_url}


async def delete_user_avatar(user_id: str):
    """删除用户头像（文件 + DB 字段）"""
    async with get_session() as session:
        user = await get_user(session, user_id)
        if not user:
            return False
        path = user.avatar_path
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
        user.avatar_path = None
        user.avatar_url = None
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return True
