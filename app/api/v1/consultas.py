from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.consulta import Consulta
from app.models.enums import EstadoCita, Rol
from app.models.signos_vitales import SignosVitales
from app.models.usuario import Usuario
from app.models.medicamento_receta import MedicamentoReceta
from app.models.receta import Receta
from app.repositories import cita as cita_repo
from app.repositories import consulta as repo
from app.repositories import receta as receta_repo
from app.repositories import signos_vitales as sv_repo
from app.schemas.consulta import ConsultaCreate, ConsultaRead, ConsultaUpdate
from app.schemas.receta import RecetaCreate, RecetaRead
from app.schemas.signos_vitales import SignosVitalesCreate, SignosVitalesRead

router = APIRouter(prefix="/consultas", tags=["Consultas"])

medico_only = require_role(Rol.MEDICO)


@router.post("", response_model=ConsultaRead, status_code=status.HTTP_201_CREATED)
async def create_consulta(
    body: ConsultaCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(medico_only),
):
    cita = await cita_repo.get_by_id(db, body.cita_id)
    if not cita:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cita no encontrada")
    if await repo.get_by_cita_id(db, body.cita_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta cita ya tiene una consulta registrada",
        )
    if cita.estado != EstadoCita.PROGRAMADA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Solo se puede registrar consulta para citas en estado PROGRAMADA",
        )
    consulta = Consulta(**body.model_dump())
    cita.estado = EstadoCita.COMPLETADA
    db.add(consulta)
    await db.commit()
    await db.refresh(consulta)
    return consulta


@router.get("/{consulta_id}", response_model=ConsultaRead)
async def get_consulta(
    consulta_id: str,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(require_role(Rol.MEDICO, Rol.ADMIN)),
):
    consulta = await repo.get_by_id(db, consulta_id)
    if not consulta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consulta no encontrada")
    return consulta


@router.patch("/{consulta_id}", response_model=ConsultaRead)
async def update_consulta(
    consulta_id: str,
    body: ConsultaUpdate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(medico_only),
):
    consulta = await repo.get_by_id(db, consulta_id)
    if not consulta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consulta no encontrada")
    if body.diagnostico is not None:
        consulta.diagnostico = body.diagnostico
    if body.notas_clinicas is not None:
        consulta.notas_clinicas = body.notas_clinicas
    if body.plan_tratamiento is not None:
        consulta.plan_tratamiento = body.plan_tratamiento
    return await repo.save(db, consulta)


@router.post(
    "/{consulta_id}/signos-vitales",
    response_model=SignosVitalesRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_signos_vitales(
    consulta_id: str,
    body: SignosVitalesCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(medico_only),
):
    consulta = await repo.get_by_id(db, consulta_id)
    if not consulta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consulta no encontrada")
    if await sv_repo.get_by_consulta_id(db, consulta_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta consulta ya tiene signos vitales registrados",
        )

    imc = None
    if body.peso and body.talla and body.talla > 0:
        imc = round(Decimal(str(body.peso)) / (Decimal(str(body.talla)) ** 2), 2)

    signos = SignosVitales(
        consulta_id=consulta_id,
        presion_arterial=body.presion_arterial,
        temperatura=body.temperatura,
        frecuencia_cardiaca=body.frecuencia_cardiaca,
        peso=body.peso,
        talla=body.talla,
        imc=imc,
    )
    return await sv_repo.create(db, signos)


@router.post(
    "/{consulta_id}/recetas",
    response_model=RecetaRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_receta(
    consulta_id: str,
    body: RecetaCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(medico_only),
):
    consulta = await repo.get_by_id(db, consulta_id)
    if not consulta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consulta no encontrada")
    if not body.medicamentos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Debe incluir al menos un medicamento",
        )
    receta = Receta(consulta_id=consulta_id)
    medicamentos = [MedicamentoReceta(**m.model_dump()) for m in body.medicamentos]
    return await receta_repo.create(db, receta, medicamentos)
