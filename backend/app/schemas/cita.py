from datetime import datetime

from pydantic import BaseModel

from app.models.enums import EstadoCita


class CitaCreate(BaseModel):
    paciente_id: str
    medico_id: str
    fecha_hora: datetime
    motivo: str | None = None


class CitaUpdate(BaseModel):
    fecha_hora: datetime | None = None
    estado: EstadoCita | None = None
    motivo: str | None = None


class CitaRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    paciente_id: str
    medico_id: str
    fecha_hora: datetime
    estado: EstadoCita
    motivo: str | None
    created_at: datetime
    updated_at: datetime
