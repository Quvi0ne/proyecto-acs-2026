from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.enums import Sexo
from app.models.paciente import Paciente
from app.repositories import consulta as consulta_repo
from app.repositories import paciente as repo
from app.web.deps import get_web_user
from app.web.templates import templates

router = APIRouter(tags=["Web"])


async def _generate_codigo(db: AsyncSession) -> str:
    year = date.today().year
    count = await repo.count_by_year(db, year)
    return f"EXP-{year}-{count + 1:05d}"


@router.get("/pacientes")
async def list_pacientes(
    request: Request,
    q: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if q:
        pacientes = await repo.search(db, q)
    else:
        pacientes = await repo.list_all(db)
    return templates.TemplateResponse(
        request, "pacientes/list.html", {"user": user, "pacientes": pacientes, "q": q}
    )


@router.get("/pacientes/crear")
async def crear_paciente_get(request: Request, user=Depends(get_web_user)):
    return templates.TemplateResponse(request, "pacientes/create.html", {"user": user, "error": None})


@router.post("/pacientes/crear")
async def crear_paciente_post(
    request: Request,
    nombre_completo: str = Form(...),
    dpi: str = Form(...),
    fecha_nacimiento: str = Form(...),
    sexo: str = Form(...),
    telefono: str = Form(""),
    email: str = Form(""),
    direccion: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if await repo.get_by_dpi(db, dpi):
        return templates.TemplateResponse(
            request,
            "pacientes/create.html",
            {"user": user, "error": "El DPI ya está registrado en el sistema"},
            status_code=409,
        )
    codigo = await _generate_codigo(db)
    paciente = Paciente(
        codigo_expediente=codigo,
        nombre_completo=nombre_completo,
        dpi=dpi,
        fecha_nacimiento=date.fromisoformat(fecha_nacimiento),
        sexo=Sexo(sexo),
        telefono=telefono or None,
        email=email or None,
        direccion=direccion or None,
    )
    try:
        await repo.create(db, paciente)
    except IntegrityError:
        return templates.TemplateResponse(
            request,
            "pacientes/create.html",
            {"user": user, "error": "Error al registrar el paciente"},
            status_code=409,
        )
    return RedirectResponse(f"/pacientes?ok=Paciente {nombre_completo} registrado", status_code=303)


@router.get("/pacientes/{paciente_id}/editar")
async def editar_paciente_get(
    paciente_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    paciente = await repo.get_by_id(db, paciente_id)
    if not paciente:
        return RedirectResponse("/pacientes?error=Paciente no encontrado", status_code=302)
    return templates.TemplateResponse(
        request, "pacientes/edit.html", {"user": user, "paciente": paciente, "error": None}
    )


@router.post("/pacientes/{paciente_id}/editar")
async def editar_paciente_post(
    paciente_id: str,
    request: Request,
    nombre_completo: str = Form(...),
    fecha_nacimiento: str = Form(...),
    sexo: str = Form(...),
    telefono: str = Form(""),
    email: str = Form(""),
    direccion: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    paciente = await repo.get_by_id(db, paciente_id)
    if not paciente:
        return RedirectResponse("/pacientes?error=Paciente no encontrado", status_code=302)
    paciente.nombre_completo = nombre_completo
    paciente.fecha_nacimiento = date.fromisoformat(fecha_nacimiento)
    paciente.sexo = Sexo(sexo)
    paciente.telefono = telefono or None
    paciente.email = email or None
    paciente.direccion = direccion or None
    paciente.updated_by = user.id
    await repo.save(db, paciente)
    return RedirectResponse(f"/pacientes/{paciente_id}?ok=Datos actualizados correctamente", status_code=303)


@router.post("/pacientes/{paciente_id}/eliminar")
async def eliminar_paciente(
    paciente_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if user.rol.value != "ADMIN":
        return RedirectResponse("/pacientes?error=Solo administradores pueden eliminar pacientes", status_code=302)
    paciente = await repo.get_by_id(db, paciente_id)
    if not paciente:
        return RedirectResponse("/pacientes?error=Paciente no encontrado", status_code=302)
    total_citas = await repo.count_citas(db, paciente_id)
    if total_citas > 0:
        return RedirectResponse(
            f"/pacientes/{paciente_id}?error=No se puede eliminar: el paciente tiene {total_citas} cita(s) registrada(s)",
            status_code=302,
        )
    nombre = paciente.nombre_completo
    await repo.delete(db, paciente_id)
    return RedirectResponse(f"/pacientes?ok=Paciente {nombre} eliminado", status_code=303)


@router.get("/pacientes/{paciente_id}")
async def detalle_paciente(
    paciente_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    paciente = await repo.get_by_id(db, paciente_id)
    if not paciente:
        return RedirectResponse("/pacientes?error=Paciente no encontrado", status_code=302)
    historial = await consulta_repo.list_historial_paciente(db, paciente_id)
    return templates.TemplateResponse(
        request, "pacientes/detail.html", {
            "user": user,
            "paciente": paciente,
            "historial": historial,
            "today": date.today(),
        }
    )
