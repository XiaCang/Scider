import asyncio
import os
import hashlib
import sys

# Try package-relative imports when running as a module; fall back to backend package imports
try:
    from ..session import get_session, create_tables_if_needed
    from ..crud_user import create_user, get_user_by_email, update_user_name, delete_user
except Exception:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
    from backend.db.session import get_session, create_tables_if_needed
    from backend.db.crud_user import create_user, get_user_by_email, update_user_name, delete_user


def hash_password(password: str) -> str:
    # simple demo hash (not for production). Use bcrypt in real app.
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


async def run_demo():
    print("DATABASE_URL:", os.getenv("DATABASE_URL"))
    if not os.getenv("DATABASE_URL"):
        print("ERROR: Please set DATABASE_URL environment variable before running")
        return

    # Create tables for quick demo (safe if tables already exist)
    await create_tables_if_needed(echo=False)

    async with get_session() as session:
        pw = hash_password("secret123")

        # 如果邮箱已存在，先删除（便于反复运行 demo）
        existing = await get_user_by_email(session, "alice@example.com")
        if existing:
            print("User with email already exists, deleting existing user:", existing.id)
            await delete_user(session, existing.id)

        print("Creating user...")
        user = await create_user(session, "alice@example.com", pw, name="Alice")
        print("Created:", user.id, user.email, user.name)

        print("Querying by email...")
        u2 = await get_user_by_email(session, "alice@example.com")
        print("Found:", u2.id, u2.email, u2.name)

        print("Updating name...")
        u3 = await update_user_name(session, user.id, "Alice Cooper")
        print("Updated:", u3.id, u3.name)

        print("Deleting user...")
        #ok = await delete_user(session, user.id)
        #print("Deleted ok:", ok)


if __name__ == "__main__":
    asyncio.run(run_demo())
