from datetime import date

from pydantic import BaseModel


class MedicamentoCreate(BaseModel):
    nombre: str
    dosis: str | None = None
    via: str | None = None
    frecuencia: str | None = None
    duracion: str | None = None


class MedicamentoRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    nombre: str
    dosis: str | None
    via: str | None
    frecuencia: str | None
    duracion: str | None


class RecetaCreate(BaseModel):
    medicamentos: list[MedicamentoCreate]


class RecetaRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    consulta_id: str
    fecha_emision: date
    medicamentos: list[MedicamentoRead]
