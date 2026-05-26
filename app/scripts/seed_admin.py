"""
Create the initial admin user if it doesn't already exist.

Usage:
    uv run python -m app.scripts.seed_admin
"""
import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.enums import Rol
from app.models.usuario import Usuario


async def seed():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Usuario).where(Usuario.email == settings.ADMIN_EMAIL))
        if result.scalar_one_or_none():
            print(f"Admin user '{settings.ADMIN_EMAIL}' already exists.")
            return

        admin = Usuario(
            nombre="Administrador",
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            rol=Rol.ADMIN,
        )
        db.add(admin)
        await db.commit()
        print(f"Admin user created: {settings.ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(seed())
