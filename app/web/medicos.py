from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories import medico as repo
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
