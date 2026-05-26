from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid


class Consulta(Base):
    __tablename__ = "consultas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cita_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("citas.id"), unique=True, nullable=False, index=True
    )
    diagnostico: Mapped[str] = mapped_column(Text, nullable=False)
    notas_clinicas: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_tratamiento: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_consulta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cita: Mapped["Cita"] = relationship("Cita", back_populates="consulta")  # noqa: F821
    signos_vitales: Mapped["SignosVitales"] = relationship(  # noqa: F821
        "SignosVitales", back_populates="consulta", uselist=False
    )
    recetas: Mapped[list["Receta"]] = relationship("Receta", back_populates="consulta")  # noqa: F821
