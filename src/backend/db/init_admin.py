"""
初始化管理员账号脚本

运行此脚本将创建默认管理员账号：
- 邮箱: admin@scider.com
- 密码: admin123456
- 姓名: Administrator

如果管理员已存在，则跳过创建。
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

from passlib.context import CryptContext
from db.session import get_session
from db.models import User
from db.crud_user import get_user_by_email, create_user

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

ADMIN_EMAIL = "admin@scider.com"
ADMIN_PASSWORD = "admin123456"
ADMIN_NAME = "Administrator"


async def init_admin():
    """初始化管理员账号"""
    async with get_session() as session:
        # 检查管理员是否已存在
        existing = await get_user_by_email(session, ADMIN_EMAIL)
        if existing:
            print(f"✅ 管理员账号已存在: {ADMIN_EMAIL}")
            return

        # 创建管理员账号
        password_hash = pwd_ctx.hash(ADMIN_PASSWORD)
        admin = await create_user(
            session=session,
            email=ADMIN_EMAIL,
            password_hash=password_hash,
            name=ADMIN_NAME
        )
        print(f"✅ 管理员账号创建成功!")
        print(f"   邮箱: {admin.email}")
        print(f"   姓名: {admin.name}")
        print(f"   ID: {admin.id}")
        print(f"\n⚠️  请妥善保管管理员密码: {ADMIN_PASSWORD}")


if __name__ == "__main__":
    try:
        asyncio.run(init_admin())
    except Exception as e:
        print(f"❌ 创建管理员失败: {e}")
        sys.exit(1)
