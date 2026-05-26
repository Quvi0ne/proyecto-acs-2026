from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paciente import Paciente


async def get_by_id(db: AsyncSession, paciente_id: str) -> Paciente | None:
    result = await db.execute(select(Paciente).where(Paciente.id == paciente_id))
    return result.scalar_one_or_none()


async def get_by_dpi(db: AsyncSession, dpi: str) -> Paciente | None:
    result = await db.execute(select(Paciente).where(Paciente.dpi == dpi))
    return result.scalar_one_or_none()


async def get_by_codigo(db: AsyncSession, codigo: str) -> Paciente | None:
    result = await db.execute(
        select(Paciente).where(Paciente.codigo_expediente == codigo)
    )
    return result.scalar_one_or_none()


async def count_by_year(db: AsyncSession, year: int) -> int:
    result = await db.execute(
        select(func.count()).where(
            func.extract("year", Paciente.created_at) == year
        )
    )
    return result.scalar_one()


async def count_all(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(Paciente))
    return result.scalar_one()


async def list_all(db: AsyncSession, limit: int = 100) -> list[Paciente]:
    result = await db.execute(
        select(Paciente).order_by(Paciente.nombre_completo).limit(limit)
    )
    return list(result.scalars().all())


async def search(db: AsyncSession, q: str, limit: int = 20) -> list[Paciente]:
    result = await db.execute(
        select(Paciente)
        .where(
            or_(
                Paciente.nombre_completo.ilike(f"%{q}%"),
                Paciente.dpi == q,
                Paciente.codigo_expediente == q,
            )
        )
        .limit(limit)
        .order_by(Paciente.nombre_completo)
    )
    return list(result.scalars().all())


async def count_citas(db: AsyncSession, paciente_id: str) -> int:
    from app.models.cita import Cita
    result = await db.execute(
        select(func.count()).where(Cita.paciente_id == paciente_id)
    )
    return result.scalar_one()


async def delete(db: AsyncSession, paciente_id: str) -> None:
    result = await db.execute(select(Paciente).where(Paciente.id == paciente_id))
    paciente = result.scalar_one_or_none()
    if paciente:
        await db.delete(paciente)
        await db.commit()


async def create(db: AsyncSession, paciente: Paciente) -> Paciente:
    db.add(paciente)
    await db.commit()
    await db.refresh(paciente)
    return paciente


async def save(db: AsyncSession, paciente: Paciente) -> Paciente:
    await db.commit()
    await db.refresh(paciente)
    return paciente
