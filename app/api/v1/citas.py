from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.cita import Cita
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.repositories import cita as repo
from app.repositories import medico as medico_repo
from app.repositories import paciente as paciente_repo
from app.models.enums import EstadoCita
from app.schemas.cita import CitaCreate, CitaRead, CitaUpdate

router = APIRouter(prefix="/citas", tags=["Citas"])

receptionist_or_admin = require_role(Rol.RECEPCIONISTA, Rol.ADMIN)


@router.post("", response_model=CitaRead, status_code=status.HTTP_201_CREATED)
async def create_cita(
    body: CitaCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(receptionist_or_admin),
):
    if not await paciente_repo.get_by_id(db, body.paciente_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado")
    if not await medico_repo.get_by_id(db, body.medico_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Médico no encontrado")
    if await repo.existe_conflicto(db, body.medico_id, body.fecha_hora):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El médico ya tiene una cita en esa fecha y hora",
        )
    cita = Cita(**body.model_dump())
    return await repo.create(db, cita)


@router.get("/{cita_id}", response_model=CitaRead)
async def get_cita(
    cita_id: str,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    cita = await repo.get_by_id(db, cita_id)
    if not cita:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")
    return cita


@router.patch("/{cita_id}", response_model=CitaRead)
async def update_cita(
    cita_id: str,
    body: CitaUpdate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(receptionist_or_admin),
):
    cita = await repo.get_by_id(db, cita_id)
    if not cita:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")
    if cita.estado != EstadoCita.PROGRAMADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Solo se pueden modificar citas en estado PROGRAMADA",
        )
    if body.estado is not None and body.estado == EstadoCita.COMPLETADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="La transición a COMPLETADA ocurre al registrar una consulta",
        )
    if body.fecha_hora is not None:
        if await repo.existe_conflicto(db, cita.medico_id, body.fecha_hora, exclude_id=cita_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El médico ya tiene una cita en esa fecha y hora",
            )
        cita.fecha_hora = body.fecha_hora
    if body.estado is not None:
        cita.estado = body.estado
    if body.motivo is not None:
        cita.motivo = body.motivo
    return await repo.save(db, cita)
