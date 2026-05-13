from pydantic import BaseModel, EmailStr

from app.models.enums import Rol


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: Rol


class UsuarioUpdateRol(BaseModel):
    rol: Rol


class UsuarioRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    nombre: str
    email: str
    rol: Rol
    activo: bool
