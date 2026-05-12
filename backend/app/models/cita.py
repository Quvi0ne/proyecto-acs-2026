from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid
from app.models.enums import EstadoCita


class Cita(Base, TimestampMixin):
    __tablename__ = "citas"
    __table_args__ = (Index("ix_citas_medico_fecha", "medico_id", "fecha_hora"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    paciente_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pacientes.id"), nullable=False
    )
    medico_id: Mapped[str] = mapped_column(String(36), ForeignKey("medicos.id"), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[EstadoCita] = mapped_column(
        Enum(EstadoCita), default=EstadoCita.PROGRAMADA, nullable=False
    )
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)

    paciente: Mapped["Paciente"] = relationship("Paciente", back_populates="citas")  # noqa: F821
    medico: Mapped["Medico"] = relationship("Medico", back_populates="citas")  # noqa: F821
    consulta: Mapped["Consulta"] = relationship("Consulta", back_populates="cita", uselist=False)  # noqa: F821
