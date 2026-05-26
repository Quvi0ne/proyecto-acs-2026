from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password
from app.models.enums import Rol
from app.models.medico import Medico
from app.models.usuario import Usuario
from app.repositories import cita as cita_repo
from app.repositories import medico as medico_repo
from app.repositories import usuario as repo
from app.web.deps import get_web_user
from app.web.templates import templates

router = APIRouter(tags=["Web"])


@router.get("/usuarios")
async def list_usuarios(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if user.rol.value != "ADMIN":
        return RedirectResponse("/?error=Acceso restringido a administradores", status_code=302)
    usuarios = await repo.list_all(db)
    active_admins = await repo.count_active_admins(db)
    return templates.TemplateResponse(
        request, "usuarios/list.html",
        {"user": user, "usuarios": usuarios, "active_admins": active_admins},
    )


@router.get("/usuarios/crear")
async def crear_usuario_get(request: Request, user=Depends(get_web_user)):
    if user.rol.value != "ADMIN":
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
    especialidad: str = Form(""),
    num_colegiado: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if user.rol.value != "ADMIN":
        return RedirectResponse("/?error=Acceso restringido a administradores", status_code=302)

    def error(msg):
        return templates.TemplateResponse(
            request, "usuarios/create.html",
            {"user": user, "error": msg},
            status_code=409,
        )

    if rol == "MEDICO":
        if not especialidad.strip() or not num_colegiado.strip():
            return error("Especialidad y número de colegiado son obligatorios para médicos")
        if await medico_repo.get_by_colegiado(db, num_colegiado.strip()):
            return error("El número de colegiado ya está registrado")

    if await repo.get_by_email(db, email):
        return error("El correo electrónico ya está registrado")

    nuevo = Usuario(
        nombre=nombre,
        email=email,
        password_hash=hash_password(password),
        rol=Rol(rol),
    )
    await repo.create(db, nuevo)

    if rol == "MEDICO":
        medico = Medico(
            usuario_id=nuevo.id,
            especialidad=especialidad.strip(),
            num_colegiado=num_colegiado.strip(),
        )
        try:
            await medico_repo.create(db, medico)
        except IntegrityError:
            return error("Error al registrar el médico")

    return RedirectResponse(f"/usuarios?ok=Usuario {nombre} creado exitosamente", status_code=303)


@router.post("/usuarios/{usuario_id}/rol")
async def cambiar_rol(
    usuario_id: str,
    request: Request,
    rol: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if user.rol.value != "ADMIN":
        return RedirectResponse("/usuarios?error=Acceso restringido a administradores", status_code=302)
    target = await repo.get_by_id(db, usuario_id)
    if not target:
        return RedirectResponse("/usuarios?error=Usuario no encontrado", status_code=302)
    target.rol = Rol(rol)
    await repo.save(db, target)
    return RedirectResponse(f"/usuarios?ok=Rol de {target.nombre} actualizado", status_code=303)


@router.post("/usuarios/{usuario_id}/eliminar")
async def eliminar_usuario(
    usuario_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if user.rol.value != "ADMIN":
        return RedirectResponse("/usuarios?error=Acceso restringido a administradores", status_code=302)
    target = await repo.get_by_id(db, usuario_id)
    if not target:
        return RedirectResponse("/usuarios?error=Usuario no encontrado", status_code=302)
    if target.id == user.id:
        return RedirectResponse("/usuarios?error=No puedes eliminar tu propia cuenta", status_code=302)
    if target.rol == Rol.ADMIN:
        active_admins = await repo.count_active_admins(db)
        if active_admins <= 1:
            return RedirectResponse(
                "/usuarios?error=No puedes eliminar al único administrador",
                status_code=302,
            )
    if target.rol == Rol.MEDICO:
        medico = await medico_repo.get_by_usuario_id(db, usuario_id)
        if medico:
            total_citas = await cita_repo.count_by_medico(db, medico.id)
            if total_citas > 0:
                return RedirectResponse(
                    f"/usuarios?error=No se puede eliminar: el médico tiene {total_citas} cita(s) registrada(s)",
                    status_code=302,
                )
            await medico_repo.delete(db, medico.id)
    nombre = target.nombre
    await repo.delete(db, usuario_id)
    return RedirectResponse(f"/usuarios?ok=Usuario {nombre} eliminado", status_code=303)
