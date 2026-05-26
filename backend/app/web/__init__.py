from fastapi import APIRouter

from app.web.auth import router as auth_router

web_router = APIRouter()
web_router.include_router(auth_router)
