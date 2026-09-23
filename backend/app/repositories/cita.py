from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cita import Cita
from app.models.enums import EstadoCita
from app.models.medico import Medico


async def list_by_fecha(db: AsyncSession, fecha: date) -> list[Cita]:
    result = await db.execute(
        select(Cita)
        .where(func.date(Cita.fecha_hora) == fecha)
        .options(
            selectinload(Cita.paciente),
            selectinload(Cita.medico).selectinload(Medico.usuario),
        )
        .order_by(Cita.fecha_hora)
    )
    return list(result.scalars().all())


async def list_all(db: AsyncSession) -> list[Cita]:
    result = await db.execute(
        select(Cita)
        .options(
            selectinload(Cita.paciente),
            selectinload(Cita.medico).selectinload(Medico.usuario),
        )
        .order_by(Cita.fecha_hora.desc())
    )
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, cita_id: str) -> Cita | None:
    result = await db.execute(
        select(Cita)
        .where(Cita.id == cita_id)
        .options(
            selectinload(Cita.paciente),
            selectinload(Cita.medico).selectinload(Medico.usuario),
        )
    )
    return result.scalar_one_or_none()


async def existe_conflicto(
    db: AsyncSession,
    medico_id: str,
    fecha_hora: datetime,
    exclude_id: str | None = None,
) -> bool:
    q = select(func.count()).where(
        Cita.medico_id == medico_id,
        Cita.fecha_hora == fecha_hora,
        Cita.estado == EstadoCita.PROGRAMADA,
    )
    if exclude_id:
        q = q.where(Cita.id != exclude_id)
    result = await db.execute(q)
    return result.scalar_one() > 0


async def count_by_medico(db: AsyncSession, medico_id: str) -> int:
    result = await db.execute(
        select(func.count()).where(Cita.medico_id == medico_id)
    )
    return result.scalar_one()


async def delete(db: AsyncSession, cita_id: str) -> None:
    result = await db.execute(select(Cita).where(Cita.id == cita_id))
    cita = result.scalar_one_or_none()
    if cita:
        await db.delete(cita)
        await db.commit()


async def create(db: AsyncSession, cita: Cita) -> Cita:
    db.add(cita)
    await db.commit()
    await db.refresh(cita)
    return cita


async def save(db: AsyncSession, cita: Cita) -> Cita:
    await db.commit()
    await db.refresh(cita)
    return cita
