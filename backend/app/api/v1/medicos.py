import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.security import hash_password
from app.models.enums import Rol
from app.models.medico import Medico
from app.models.usuario import Usuario
from app.repositories import medico as repo
from app.repositories import usuario as usuario_repo
from app.schemas.medico import MedicoCreate, MedicoRead

router = APIRouter(prefix="/medicos", tags=["Medicos"])

admin_only = require_role(Rol.ADMIN)


@router.post("", response_model=MedicoRead, status_code=status.HTTP_201_CREATED)
async def create_medico(
    body: MedicoCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    if await repo.get_by_colegiado(db, body.num_colegiado):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Número de colegiado ya registrado",
        )

    email = body.email or f"medico_{body.num_colegiado}@sece.local"
    existing_user = await usuario_repo.get_by_email(db, email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")

    password = body.password or "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(12)
    )
    user = Usuario(
        nombre=body.nombre,
        email=email,
        password_hash=hash_password(password),
        rol=Rol.MEDICO,
    )
    await usuario_repo.create(db, user)

    medico = Medico(
        usuario_id=user.id,
        especialidad=body.especialidad,
        num_colegiado=body.num_colegiado,
    )
    return await repo.create(db, medico)


@router.get("", response_model=list[MedicoRead])
async def list_medicos(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await repo.list_active(db)
