from pydantic import BaseModel, EmailStr


class MedicoCreate(BaseModel):
    nombre: str
    especialidad: str
    num_colegiado: str
    email: EmailStr | None = None
    password: str | None = None


class MedicoRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    especialidad: str
    num_colegiado: str
    activo: bool
    usuario_id: str
