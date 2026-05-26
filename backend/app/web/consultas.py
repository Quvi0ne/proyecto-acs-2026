from decimal import Decimal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.consulta import Consulta
from app.models.enums import EstadoCita
from app.models.medicamento_receta import MedicamentoReceta
from app.models.receta import Receta
from app.models.signos_vitales import SignosVitales
from app.repositories import cita as cita_repo
from app.repositories import consulta as repo
from app.repositories import receta as receta_repo
from app.repositories import signos_vitales as sv_repo
from app.web.deps import get_web_user
from app.web.templates import templates

router = APIRouter(tags=["Web"])


@router.get("/consultas/crear")
async def crear_consulta_get(
    request: Request,
    cita_id: str = "",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    cita = await cita_repo.get_by_id(db, cita_id) if cita_id else None
    return templates.TemplateResponse(
        request, "consultas/create.html", {"user": user, "cita": cita, "cita_id": cita_id, "error": None}
    )


@router.post("/consultas/crear")
async def crear_consulta_post(
    request: Request,
    cita_id: str = Form(...),
    diagnostico: str = Form(...),
    notas_clinicas: str = Form(""),
    plan_tratamiento: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    cita = await cita_repo.get_by_id(db, cita_id)
    if not cita:
        return RedirectResponse("/citas?error=Cita no encontrada", status_code=302)
    if await repo.get_by_cita_id(db, cita_id):
        return RedirectResponse("/citas?error=Esta cita ya tiene una consulta registrada", status_code=302)
    if cita.estado != EstadoCita.PROGRAMADA:
        return RedirectResponse("/citas?error=La cita no está en estado PROGRAMADA", status_code=302)

    consulta = Consulta(
        cita_id=cita_id,
        diagnostico=diagnostico,
        notas_clinicas=notas_clinicas or None,
        plan_tratamiento=plan_tratamiento or None,
    )
    cita.estado = EstadoCita.COMPLETADA
    db.add(consulta)
    await db.commit()
    await db.refresh(consulta)
    return RedirectResponse(f"/consultas/{consulta.id}?ok=Consulta registrada", status_code=303)


@router.get("/consultas/{consulta_id}")
async def detalle_consulta(
    consulta_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    consulta = await repo.get_by_id_with_relations(db, consulta_id)
    if not consulta:
        return RedirectResponse("/pacientes?error=Consulta no encontrada", status_code=302)
    return templates.TemplateResponse(
        request, "consultas/detail.html", {"user": user, "consulta": consulta}
    )


@router.get("/consultas/{consulta_id}/signos")
async def signos_get(
    consulta_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    consulta = await repo.get_by_id(db, consulta_id)
    if not consulta:
        return RedirectResponse("/pacientes?error=Consulta no encontrada", status_code=302)
    return templates.TemplateResponse(
        request, "consultas/signos.html", {"user": user, "consulta": consulta, "error": None}
    )


@router.post("/consultas/{consulta_id}/signos")
async def signos_post(
    consulta_id: str,
    presion_arterial: str = Form(""),
    temperatura: str = Form(""),
    frecuencia_cardiaca: str = Form(""),
    peso: str = Form(""),
    talla: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    consulta = await repo.get_by_id(db, consulta_id)
    if not consulta:
        return RedirectResponse("/pacientes?error=Consulta no encontrada", status_code=302)
    if await sv_repo.get_by_consulta_id(db, consulta_id):
        return RedirectResponse(
            f"/consultas/{consulta_id}?error=Ya tiene signos vitales registrados", status_code=302
        )

    peso_f = float(peso) if peso else None
    talla_f = float(talla) if talla else None
    imc = None
    if peso_f and talla_f and talla_f > 0:
        imc = round(Decimal(str(peso_f)) / (Decimal(str(talla_f)) ** 2), 2)

    signos = SignosVitales(
        consulta_id=consulta_id,
        presion_arterial=presion_arterial or None,
        temperatura=float(temperatura) if temperatura else None,
        frecuencia_cardiaca=int(frecuencia_cardiaca) if frecuencia_cardiaca else None,
        peso=peso_f,
        talla=talla_f,
        imc=imc,
    )
    await sv_repo.create(db, signos)
    return RedirectResponse(f"/consultas/{consulta_id}?ok=Signos vitales registrados", status_code=303)


@router.get("/consultas/{consulta_id}/receta")
async def receta_get(
    consulta_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    consulta = await repo.get_by_id(db, consulta_id)
    if not consulta:
        return RedirectResponse("/pacientes?error=Consulta no encontrada", status_code=302)
    return templates.TemplateResponse(
        request, "consultas/receta.html", {"user": user, "consulta": consulta, "error": None}
    )


@router.post("/consultas/{consulta_id}/receta")
async def receta_post(
    consulta_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    form = await request.form()
    nombres = form.getlist("nombre[]")
    dosis_list = form.getlist("dosis[]")
    via_list = form.getlist("via[]")
    frecuencia_list = form.getlist("frecuencia[]")
    duracion_list = form.getlist("duracion[]")

    consulta = await repo.get_by_id(db, consulta_id)
    if not consulta:
        return RedirectResponse("/pacientes?error=Consulta no encontrada", status_code=302)
    nombres_validos = [n.strip() for n in nombres if n.strip()]
    if not nombres_validos:
        return templates.TemplateResponse(
            request,
            "consultas/receta.html",
            {"user": user, "consulta": consulta, "error": "Agrega al menos un medicamento"},
            status_code=422,
        )

    receta = Receta(consulta_id=consulta_id)
    medicamentos = [
        MedicamentoReceta(
            nombre=nombres[i].strip(),
            dosis=dosis_list[i] if i < len(dosis_list) and dosis_list[i] else None,
            via=via_list[i] if i < len(via_list) and via_list[i] else None,
            frecuencia=frecuencia_list[i] if i < len(frecuencia_list) and frecuencia_list[i] else None,
            duracion=duracion_list[i] if i < len(duracion_list) and duracion_list[i] else None,
        )
        for i in range(len(nombres))
        if nombres[i].strip()
    ]
    await receta_repo.create(db, receta, medicamentos)
    return RedirectResponse(f"/consultas/{consulta_id}?ok=Receta emitida", status_code=303)
