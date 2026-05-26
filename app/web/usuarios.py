from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.repositories import usuario as repo
from app.web.deps import get_web_user
from app.web.templates import templates

router = APIRouter(tags=["Web"])


def _admin_only(user) -> bool:
    return user.rol.value == "ADMIN"


@router.get("/usuarios")
async def list_usuarios(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if not _admin_only(user):
        return RedirectResponse("/?error=Acceso restringido a administradores", status_code=302)
    usuarios = await repo.list_all(db)
    return templates.TemplateResponse(
        request, "usuarios/list.html", {"user": user, "usuarios": usuarios}
    )


@router.get("/usuarios/crear")
async def crear_usuario_get(request: Request, user=Depends(get_web_user)):
    if not _admin_only(user):
        return RedirectResponse("/?error=Acceso restringido a administradores", status_code=302)
    return templates.TemplateResponse(
        request, "usuarios/create.html", {"user": user, "error": None}
    )


@router.post("/usuarios/crear")
async def crear_usuario_post(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    rol: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if not _admin_only(user):
        return RedirectResponse("/?error=Acceso restringido a administradores", status_code=302)
    if await repo.get_by_email(db, email):
        return templates.TemplateResponse(
            request, "usuarios/create.html",
            {"user": user, "error": "El correo electrónico ya está registrado"},
            status_code=409,
        )
    nuevo = Usuario(
        nombre=nombre,
        email=email,
        password_hash=hash_password(password),
        rol=Rol(rol),
    )
    await repo.create(db, nuevo)
    return RedirectResponse(f"/usuarios?ok=Usuario {nombre} creado exitosamente", status_code=303)


@router.post("/usuarios/{usuario_id}/rol")
async def cambiar_rol(
    usuario_id: str,
    request: Request,
    rol: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if not _admin_only(user):
        return RedirectResponse("/usuarios?error=Acceso restringido a administradores", status_code=302)
    target = await repo.get_by_id(db, usuario_id)
    if not target:
        return RedirectResponse("/usuarios?error=Usuario no encontrado", status_code=302)
    target.rol = Rol(rol)
    await repo.save(db, target)
    return RedirectResponse(f"/usuarios?ok=Rol de {target.nombre} actualizado", status_code=303)


@router.post("/usuarios/{usuario_id}/activo")
async def toggle_activo(
    usuario_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if not _admin_only(user):
        return RedirectResponse("/usuarios?error=Acceso restringido a administradores", status_code=302)
    target = await repo.get_by_id(db, usuario_id)
    if not target:
        return RedirectResponse("/usuarios?error=Usuario no encontrado", status_code=302)
    if target.id == user.id:
        return RedirectResponse("/usuarios?error=No puedes desactivar tu propia cuenta", status_code=302)
    target.activo = not target.activo
    accion = "activado" if target.activo else "desactivado"
    await repo.save(db, target)
    return RedirectResponse(f"/usuarios?ok=Usuario {target.nombre} {accion}", status_code=303)
