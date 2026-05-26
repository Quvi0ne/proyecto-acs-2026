import secrets
import string

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import hash_password
from app.models.enums import Rol
from app.models.medico import Medico
from app.models.usuario import Usuario
from app.repositories import medico as repo
from app.repositories import usuario as usuario_repo
from app.web.deps import get_web_user
from app.web.templates import templates

router = APIRouter(tags=["Web"])


@router.get("/medicos")
async def list_medicos(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    medicos = await repo.list_active(db)
    return templates.TemplateResponse(
        request, "medicos/list.html", {"user": user, "medicos": medicos}
    )


@router.post("/medicos/{medico_id}/desactivar")
async def desactivar_medico(
    medico_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if user.rol.value != "ADMIN":
        return RedirectResponse("/medicos?error=Solo administradores pueden desactivar médicos", status_code=302)
    medico = await repo.get_by_id(db, medico_id)
    if not medico:
        return RedirectResponse("/medicos?error=Médico no encontrado", status_code=302)
    medico.activo = False
    await repo.save(db, medico)
    return RedirectResponse("/medicos?ok=Médico desactivado", status_code=303)


@router.get("/medicos/crear")
async def crear_medico_get(request: Request, user=Depends(get_web_user)):
    if user.rol.value != "ADMIN":
        return RedirectResponse("/medicos?error=Acceso restringido a administradores", status_code=302)
    return templates.TemplateResponse(
        request, "medicos/create.html", {"user": user, "error": None}
    )


@router.post("/medicos/crear")
async def crear_medico_post(
    request: Request,
    nombre: str = Form(...),
    especialidad: str = Form(...),
    num_colegiado: str = Form(...),
    email: str = Form(""),
    password: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if user.rol.value != "ADMIN":
        return RedirectResponse("/medicos?error=Acceso restringido a administradores", status_code=302)

    if await repo.get_by_colegiado(db, num_colegiado):
        return templates.TemplateResponse(
            request, "medicos/create.html",
            {"user": user, "error": "El número de colegiado ya está registrado"},
            status_code=409,
        )

    email_final = email.strip() or f"medico_{num_colegiado}@sece.local"
    if await usuario_repo.get_by_email(db, email_final):
        return templates.TemplateResponse(
            request, "medicos/create.html",
            {"user": user, "error": "El correo electrónico ya está en uso"},
            status_code=409,
        )

    pwd = password.strip() or "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(12)
    )
    nuevo_usuario = Usuario(
        nombre=nombre,
        email=email_final,
        password_hash=hash_password(pwd),
        rol=Rol.MEDICO,
    )
    await usuario_repo.create(db, nuevo_usuario)

    medico = Medico(
        usuario_id=nuevo_usuario.id,
        especialidad=especialidad,
        num_colegiado=num_colegiado,
    )
    try:
        await repo.create(db, medico)
    except IntegrityError:
        return templates.TemplateResponse(
            request, "medicos/create.html",
            {"user": user, "error": "Error al registrar el médico"},
            status_code=409,
        )
    return RedirectResponse(f"/medicos?ok=Médico {nombre} registrado exitosamente", status_code=303)
