from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from .models import Folder, Paper


async def create_folder(
    session: AsyncSession,
    user_id: str,
    name: str,
) -> Folder:
    """Create a new folder for the given user."""
    folder = Folder(user_id=user_id, name=name)
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    return folder


async def get_folder_by_id(
    session: AsyncSession,
    folder_id: str,
) -> Optional[Folder]:
    """Get a single folder by its id."""
    q = select(Folder).where(Folder.id == folder_id)
    res = await session.execute(q)
    return res.scalars().first()


async def get_folders_by_user(
    session: AsyncSession,
    user_id: str,
) -> list[Folder]:
    """List all folders belonging to a user, ordered by creation time."""
    q = (
        select(Folder)
        .where(Folder.user_id == user_id)
        .order_by(Folder.created_at.desc())
    )
    res = await session.execute(q)
    return list(res.scalars().all())


async def update_folder_name(
    session: AsyncSession,
    folder_id: str,
    name: str,
) -> Optional[Folder]:
    """Rename a folder. Returns None if folder not found."""
    folder = await get_folder_by_id(session, folder_id)
    if not folder:
        return None
    folder.name = name
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    return folder


async def delete_folder(
    session: AsyncSession,
    folder_id: str,
) -> bool:
    """Delete a folder by id.
    Papers in the folder will have their folder_id set to NULL.
    Returns True if deleted, False if not found.
    """
    folder = await get_folder_by_id(session, folder_id)
    if not folder:
        return False

    # Detach papers from this folder before deleting
    q = select(Paper).where(Paper.folder_id == folder_id)
    res = await session.execute(q)
    papers = list(res.scalars().all())
    for p in papers:
        p.folder_id = None

    await session.delete(folder)
    await session.commit()
    return True
