from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.repositories import cita as cita_repo
from app.repositories import medico as medico_repo
from app.repositories import paciente as paciente_repo
from app.repositories import usuario as usuario_repo
from app.web.deps import get_web_user
from app.web.templates import templates

router = APIRouter(tags=["Web"])


@router.get("/login")
async def login_get(request: Request):
    return templates.TemplateResponse(request, "login.html", {"user": None, "error": None})


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    user = await usuario_repo.get_by_email(db, email)
    if not user or not user.activo or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"user": None, "error": "Correo o contraseña incorrectos"},
            status_code=401,
        )
    token = create_access_token(sub=user.id, rol=user.rol.value)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("sece_token", token, httponly=True, samesite="lax")
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("sece_token")
    return response


@router.get("/")
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    hoy = date.today()
    citas_hoy = await cita_repo.list_by_fecha(db, hoy)
    total_pacientes = await paciente_repo.count_all(db)
    medicos = await medico_repo.list_active(db)
    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "citas_hoy": citas_hoy,
        "total_pacientes": total_pacientes,
        "total_medicos": len(medicos),
    })
