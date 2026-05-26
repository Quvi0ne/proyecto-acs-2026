from datetime import datetime

from pydantic import BaseModel


class ConsultaCreate(BaseModel):
    cita_id: str
    diagnostico: str
    notas_clinicas: str | None = None
    plan_tratamiento: str | None = None


class ConsultaRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    cita_id: str
    diagnostico: str
    notas_clinicas: str | None
    plan_tratamiento: str | None
    fecha_consulta: datetime


class ConsultaUpdate(BaseModel):
    diagnostico: str | None = None
    notas_clinicas: str | None = None
    plan_tratamiento: str | None = None


class ConsultaHistorial(BaseModel):
    id: str
    fecha_consulta: datetime
    medico_nombre: str
    diagnostico: str
