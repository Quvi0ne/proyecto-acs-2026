from datetime import date

from pydantic import BaseModel, EmailStr

from app.models.enums import Sexo


class PacienteCreate(BaseModel):
    nombre_completo: str
    dpi: str
    fecha_nacimiento: date
    sexo: Sexo
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None


class PacienteUpdate(BaseModel):
    nombre_completo: str | None = None
    fecha_nacimiento: date | None = None
    sexo: Sexo | None = None
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None


class PacienteRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    codigo_expediente: str
    nombre_completo: str
    dpi: str
    fecha_nacimiento: date
    sexo: Sexo
    telefono: str | None
    email: str | None
    direccion: str | None


class PacienteSearchResult(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    codigo_expediente: str
    nombre_completo: str
    dpi: str
