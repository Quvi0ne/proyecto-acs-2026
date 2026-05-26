from pydantic import BaseModel


class SignosVitalesCreate(BaseModel):
    presion_arterial: str | None = None
    temperatura: float | None = None
    frecuencia_cardiaca: int | None = None
    peso: float | None = None
    talla: float | None = None


class SignosVitalesRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    consulta_id: str
    presion_arterial: str | None
    temperatura: float | None
    frecuencia_cardiaca: int | None
    peso: float | None
    talla: float | None
    imc: float | None
