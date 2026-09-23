from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.usuario import Usuario
from app.repositories import usuario as usuario_repo


class WebAuthException(Exception):
    pass


async def get_web_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    token = request.cookies.get("sece_token")
    if not token:
        raise WebAuthException()
    payload = decode_token(token)
    if not payload:
        raise WebAuthException()
    user = await usuario_repo.get_by_id(db, payload["sub"])
    if not user or not user.activo:
        raise WebAuthException()
    return user
