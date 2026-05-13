from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.security import hash_password
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.repositories import usuario as repo
from app.schemas.usuario import UsuarioCreate, UsuarioRead, UsuarioUpdateRol

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

admin_only = require_role(Rol.ADMIN)


@router.get("", response_model=list[UsuarioRead])
async def list_usuarios(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    return await repo.list_all(db)


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    body: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    existing = await repo.get_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email ya registrado")

    user = Usuario(
        nombre=body.nombre,
        email=body.email,
        password_hash=hash_password(body.password),
        rol=body.rol,
    )
    return await repo.create(db, user)


@router.patch("/{user_id}/rol", response_model=UsuarioRead)
async def update_rol(
    user_id: str,
    body: UsuarioUpdateRol,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(admin_only),
):
    user = await repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    user.rol = body.rol
    return await repo.save(db, user)


@router.patch("/{user_id}/activo", response_model=UsuarioRead)
async def toggle_activo(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current: Usuario = Depends(admin_only),
):
    user = await repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if user.id == current.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes desactivar tu propia cuenta")
    user.activo = not user.activo
    return await repo.save(db, user)


@router.get("/me", response_model=UsuarioRead)
async def me(current: Usuario = Depends(get_current_user)):
    return current
