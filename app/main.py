from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine, get_db
from app.core.security import hash_password
from app.models import Base
from app.models.enums import Rol
from app.models.usuario import Usuario
from app.web import web_router
from app.web.deps import WebAuthException


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Usuario).where(Usuario.email == settings.ADMIN_EMAIL))
        if not result.scalar_one_or_none():
            db.add(Usuario(
                nombre="Administrador",
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                rol=Rol.ADMIN,
            ))
            await db.commit()
    yield


app = FastAPI(
    title="SECE API",
    description="Sistema de Expediente Clínico Electrónico",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(WebAuthException)
async def web_auth_handler(request: Request, exc: WebAuthException):
    return RedirectResponse("/login", status_code=302)


app.include_router(web_router)
app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}
