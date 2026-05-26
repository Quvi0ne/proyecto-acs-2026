from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.enums import Rol
from app.models.paciente import Paciente
from app.models.usuario import Usuario
from app.repositories import consulta as consulta_repo
from app.repositories import paciente as repo
from app.schemas.consulta import ConsultaHistorial
from app.schemas.paciente import PacienteCreate, PacienteRead, PacienteSearchResult, PacienteUpdate

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])

receptionist_or_admin = require_role(Rol.RECEPCIONISTA, Rol.ADMIN)


async def _generate_codigo(db: AsyncSession) -> str:
    year = date.today().year
    count = await repo.count_by_year(db, year)
    return f"EXP-{year}-{count + 1:05d}"


@router.post("", response_model=PacienteRead, status_code=status.HTTP_201_CREATED)
async def create_paciente(
    body: PacienteCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(receptionist_or_admin),
):
    if await repo.get_by_dpi(db, body.dpi):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="DPI ya registrado en el sistema")

    codigo = await _generate_codigo(db)
    paciente = Paciente(codigo_expediente=codigo, **body.model_dump())
    return await repo.create(db, paciente)


@router.get("", response_model=list[PacienteSearchResult])
async def search_pacientes(
    q: str = Query(..., min_length=1, description="Nombre parcial, DPI exacto, o código de expediente"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await repo.search(db, q, limit)


@router.get("/{paciente_id}", response_model=PacienteRead)
async def get_paciente(
    paciente_id: str,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    paciente = await repo.get_by_id(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado")
    return paciente


@router.patch("/{paciente_id}", response_model=PacienteRead)
async def update_paciente(
    paciente_id: str,
    body: PacienteUpdate,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(receptionist_or_admin),
):
    paciente = await repo.get_by_id(db, paciente_id)
    if not paciente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(paciente, field, value)

    paciente.updated_by = current.id
    return await repo.save(db, paciente)


@router.get("/{paciente_id}/consultas", response_model=list[ConsultaHistorial])
async def historial_consultas(
    paciente_id: str,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    if not await repo.get_by_id(db, paciente_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado")
    return await consulta_repo.list_historial_paciente(db, paciente_id)
