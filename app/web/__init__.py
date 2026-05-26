from fastapi import APIRouter

from app.web.auth import router as auth_router
from app.web.citas import router as citas_router
from app.web.consultas import router as consultas_router
from app.web.medicos import router as medicos_router
from app.web.pacientes import router as pacientes_router
from app.web.usuarios import router as usuarios_router

web_router = APIRouter()
web_router.include_router(auth_router)
web_router.include_router(pacientes_router)
web_router.include_router(citas_router)
web_router.include_router(consultas_router)
web_router.include_router(medicos_router)
web_router.include_router(usuarios_router)
