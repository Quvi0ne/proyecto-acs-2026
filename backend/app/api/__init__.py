from fastapi import APIRouter

from app.api.v1 import auth, citas, consultas, medicos, pacientes, recetas, usuarios

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(pacientes.router)
api_router.include_router(medicos.router)
api_router.include_router(citas.router)
api_router.include_router(consultas.router)
api_router.include_router(recetas.router)
