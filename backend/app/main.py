from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import api_router
from app.core.database import get_db
from app.web import web_router
from app.web.deps import WebAuthException

app = FastAPI(
    title="SECE API",
    description="Sistema de Expediente Clínico Electrónico",
    version="0.1.0",
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
