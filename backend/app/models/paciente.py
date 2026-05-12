from datetime import date

from sqlalchemy import Date, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid
from app.models.enums import Sexo


class Paciente(Base, TimestampMixin):
    __tablename__ = "pacientes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    codigo_expediente: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    dpi: Mapped[str] = mapped_column(String(13), unique=True, nullable=False, index=True)
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    sexo: Mapped[Sexo] = mapped_column(Enum(Sexo), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(15), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    citas: Mapped[list["Cita"]] = relationship("Cita", back_populates="paciente")  # noqa: F821
