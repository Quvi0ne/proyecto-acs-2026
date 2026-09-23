from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories import cita as cita_repo
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


@router.post("/medicos/{medico_id}/eliminar")
async def eliminar_medico(
    medico_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_web_user),
):
    if user.rol.value != "ADMIN":
        return RedirectResponse("/medicos?error=Solo administradores pueden eliminar médicos", status_code=302)
    medico = await repo.get_by_id(db, medico_id)
    if not medico:
        return RedirectResponse("/medicos?error=Médico no encontrado", status_code=302)
    total_citas = await cita_repo.count_by_medico(db, medico_id)
    if total_citas > 0:
        return RedirectResponse(
            f"/medicos?error=No se puede eliminar: el médico tiene {total_citas} cita(s) registrada(s)",
            status_code=302,
        )
    usuario_id = medico.usuario_id
    await repo.delete(db, medico_id)
    await usuario_repo.delete(db, usuario_id)
    return RedirectResponse("/medicos?ok=Médico eliminado", status_code=303)
