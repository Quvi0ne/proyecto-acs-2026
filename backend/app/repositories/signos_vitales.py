from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signos_vitales import SignosVitales


async def get_by_consulta_id(db: AsyncSession, consulta_id: str) -> SignosVitales | None:
    result = await db.execute(
        select(SignosVitales).where(SignosVitales.consulta_id == consulta_id)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, signos: SignosVitales) -> SignosVitales:
    db.add(signos)
    await db.commit()
    await db.refresh(signos)
    return signos
