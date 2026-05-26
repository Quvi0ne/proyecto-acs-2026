from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cita import Cita
from app.models.consulta import Consulta
from app.models.medico import Medico
from app.models.receta import Receta
from app.models.usuario import Usuario


async def get_by_id(db: AsyncSession, consulta_id: str) -> Consulta | None:
    result = await db.execute(select(Consulta).where(Consulta.id == consulta_id))
    return result.scalar_one_or_none()


async def get_by_id_with_relations(db: AsyncSession, consulta_id: str) -> Consulta | None:
    result = await db.execute(
        select(Consulta)
        .where(Consulta.id == consulta_id)
        .options(
            selectinload(Consulta.cita).selectinload(Cita.paciente),
            selectinload(Consulta.cita).selectinload(Cita.medico).selectinload(Medico.usuario),
            selectinload(Consulta.signos_vitales),
            selectinload(Consulta.recetas).selectinload(Receta.medicamentos),
        )
    )
    return result.scalar_one_or_none()


async def get_by_cita_id(db: AsyncSession, cita_id: str) -> Consulta | None:
    result = await db.execute(select(Consulta).where(Consulta.cita_id == cita_id))
    return result.scalar_one_or_none()


async def list_historial_paciente(db: AsyncSession, paciente_id: str) -> list[dict]:
    result = await db.execute(
        select(
            Consulta.id.label("id"),
            Consulta.fecha_consulta.label("fecha_consulta"),
            Consulta.diagnostico.label("diagnostico"),
            Usuario.nombre.label("medico_nombre"),
        )
        .join(Cita, Consulta.cita_id == Cita.id)
        .join(Medico, Cita.medico_id == Medico.id)
        .join(Usuario, Medico.usuario_id == Usuario.id)
        .where(Cita.paciente_id == paciente_id)
        .order_by(Consulta.fecha_consulta.desc())
    )
    return [row._asdict() for row in result.all()]


async def create(db: AsyncSession, consulta: Consulta) -> Consulta:
    db.add(consulta)
    await db.commit()
    await db.refresh(consulta)
    return consulta


async def save(db: AsyncSession, consulta: Consulta) -> Consulta:
    await db.commit()
    await db.refresh(consulta)
    return consulta
