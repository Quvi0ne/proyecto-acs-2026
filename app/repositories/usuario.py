from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Rol
from app.models.usuario import Usuario


async def get_by_id(db: AsyncSession, user_id: str) -> Usuario | None:
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> Usuario | None:
    result = await db.execute(select(Usuario).where(Usuario.email == email))
    return result.scalar_one_or_none()


async def count_active_admins(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).where(Usuario.rol == Rol.ADMIN, Usuario.activo == True)  # noqa: E712
    )
    return result.scalar_one()


async def list_all(db: AsyncSession) -> list[Usuario]:
    result = await db.execute(select(Usuario).order_by(Usuario.nombre))
    return list(result.scalars().all())


async def delete(db: AsyncSession, user_id: str) -> None:
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    usuario = result.scalar_one_or_none()
    if usuario:
        await db.delete(usuario)
        await db.commit()


async def create(db: AsyncSession, usuario: Usuario) -> Usuario:
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)
    return usuario


async def save(db: AsyncSession, usuario: Usuario) -> Usuario:
    await db.commit()
    await db.refresh(usuario)
    return usuario
