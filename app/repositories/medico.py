from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.medico import Medico


async def get_by_id(db: AsyncSession, medico_id: str) -> Medico | None:
    result = await db.execute(select(Medico).where(Medico.id == medico_id))
    return result.scalar_one_or_none()


async def get_by_colegiado(db: AsyncSession, num_colegiado: str) -> Medico | None:
    result = await db.execute(select(Medico).where(Medico.num_colegiado == num_colegiado))
    return result.scalar_one_or_none()


async def list_active(db: AsyncSession) -> list[Medico]:
    result = await db.execute(
        select(Medico)
        .where(Medico.activo == True)  # noqa: E712
        .options(selectinload(Medico.usuario))
        .order_by(Medico.id)
    )
    return list(result.scalars().all())


async def get_by_usuario_id(db: AsyncSession, usuario_id: str) -> Medico | None:
    result = await db.execute(select(Medico).where(Medico.usuario_id == usuario_id))
    return result.scalar_one_or_none()


async def delete(db: AsyncSession, medico_id: str) -> None:
    result = await db.execute(select(Medico).where(Medico.id == medico_id))
    medico = result.scalar_one_or_none()
    if medico:
        await db.delete(medico)
        await db.commit()


async def save(db: AsyncSession, medico: Medico) -> Medico:
    await db.commit()
    await db.refresh(medico)
    return medico


async def create(db: AsyncSession, medico: Medico) -> Medico:
    db.add(medico)
    await db.commit()
    await db.refresh(medico)
    return medico
