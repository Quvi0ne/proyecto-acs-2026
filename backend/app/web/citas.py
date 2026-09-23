from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.cita import Cita
from app.models.enums import EstadoCita
from app.repositories import cita as repo
from app.repositories import medico as medico_repo
from app.repositories import paciente as paciente_repo
from app.web.deps import get_web_user
from app.web.templates import templates

router = APIRouter(tags=["Web"])


@router.get("/citas")
async def list_citas(
    request: Request,
    fecha: str = "",
    todas: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if todas:
        citas = await repo.list_all(db)
        return templates.TemplateResponse(
            request, "citas/list.html", {"user": user, "citas": citas, "fecha": "", "todas": True}
        )
    hoy = date.fromisoformat(fecha) if fecha else date.today()
    citas = await repo.list_by_fecha(db, hoy)
    return templates.TemplateResponse(
        request, "citas/list.html", {"user": user, "citas": citas, "fecha": hoy, "todas": False}
    )


@router.get("/citas/crear")
async def crear_cita_get(
    request: Request,
    paciente_id: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    pacientes = await paciente_repo.list_all(db)
    medicos = await medico_repo.list_active(db)
    return templates.TemplateResponse(
        request,
        "citas/create.html",
        {"user": user, "pacientes": pacientes, "medicos": medicos,
         "paciente_id_sel": paciente_id, "error": None},
    )


@router.post("/citas/crear")
async def crear_cita_post(
    request: Request,
    paciente_id: str = Form(...),
    medico_id: str = Form(...),
    fecha_hora: str = Form(...),
    motivo: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    try:
        dt = datetime.fromisoformat(fecha_hora).replace(tzinfo=timezone.utc)
    except ValueError:
        dt = datetime.fromisoformat(fecha_hora + ":00").replace(tzinfo=timezone.utc)

    if await repo.existe_conflicto(db, medico_id, dt):
        pacientes = await paciente_repo.list_all(db)
        medicos = await medico_repo.list_active(db)
        return templates.TemplateResponse(
            request,
            "citas/create.html",
            {"user": user, "pacientes": pacientes, "medicos": medicos,
             "paciente_id_sel": paciente_id,
             "error": "El médico ya tiene una cita programada a esa hora"},
            status_code=409,
        )

    cita = Cita(paciente_id=paciente_id, medico_id=medico_id, fecha_hora=dt, motivo=motivo or None)
    await repo.create(db, cita)
    return RedirectResponse(f"/citas?ok=Cita programada exitosamente&fecha={dt.date()}", status_code=303)


@router.post("/citas/{cita_id}/eliminar")
async def eliminar_cita(
    cita_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    cita = await repo.get_by_id(db, cita_id)
    if not cita:
        return RedirectResponse("/citas?error=Cita no encontrada", status_code=302)
    if cita.estado == EstadoCita.COMPLETADA:
        return RedirectResponse(
            "/citas?error=No se puede eliminar una cita completada (tiene consulta asociada)",
            status_code=302,
        )
    await repo.delete(db, cita_id)
    return RedirectResponse("/citas?ok=Cita eliminada", status_code=303)


@router.get("/citas/{cita_id}/editar")
async def editar_cita_get(
    cita_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    cita = await repo.get_by_id(db, cita_id)
    if not cita:
        return RedirectResponse("/citas?error=Cita no encontrada", status_code=302)
    return templates.TemplateResponse(
        request, "citas/edit.html", {"user": user, "cita": cita, "error": None}
    )


@router.post("/citas/{cita_id}/editar")
async def editar_cita_post(
    cita_id: str,
    request: Request,
    accion: str = Form(...),
    fecha_hora: str = Form(""),
    motivo: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    cita = await repo.get_by_id(db, cita_id)
    if not cita:
        return RedirectResponse("/citas?error=Cita no encontrada", status_code=302)
    if cita.estado != EstadoCita.PROGRAMADA:
        return RedirectResponse(
            "/citas?error=Solo se pueden modificar citas en estado PROGRAMADA", status_code=302
        )

    if accion == "cancelar":
        cita.estado = EstadoCita.CANCELADA
        cita.motivo = motivo or cita.motivo
        await repo.save(db, cita)
        return RedirectResponse("/citas?ok=Cita cancelada", status_code=303)

    if accion == "reprogramar" and fecha_hora:
        try:
            dt = datetime.fromisoformat(fecha_hora).replace(tzinfo=timezone.utc)
        except ValueError:
            dt = datetime.fromisoformat(fecha_hora + ":00").replace(tzinfo=timezone.utc)
        if await repo.existe_conflicto(db, cita.medico_id, dt, exclude_id=cita_id):
            return templates.TemplateResponse(
                request,
                "citas/edit.html",
                {"user": user, "cita": cita, "error": "El médico ya tiene una cita a esa hora"},
                status_code=409,
            )
        cita.fecha_hora = dt
        await repo.save(db, cita)
        return RedirectResponse(f"/citas?ok=Cita reprogramada&fecha={dt.date()}", status_code=303)

    return RedirectResponse("/citas", status_code=302)
