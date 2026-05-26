from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.medicamento_receta import MedicamentoReceta
from app.models.receta import Receta


async def get_by_id(db: AsyncSession, receta_id: str) -> Receta | None:
    result = await db.execute(
        select(Receta)
        .where(Receta.id == receta_id)
        .options(selectinload(Receta.medicamentos))
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, receta: Receta, medicamentos: list[MedicamentoReceta]) -> Receta:
    db.add(receta)
    await db.flush()
    for m in medicamentos:
        m.receta_id = receta.id
        db.add(m)
    await db.commit()
    return await get_by_id(db, receta.id)
