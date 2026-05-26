from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.usuario import Usuario
from app.repositories import receta as repo
from app.schemas.receta import RecetaRead

router = APIRouter(prefix="/recetas", tags=["Recetas"])


@router.get("/{receta_id}", response_model=RecetaRead)
async def get_receta(
    receta_id: str,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    receta = await repo.get_by_id(db, receta_id)
    if not receta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receta no encontrada")
    return receta
