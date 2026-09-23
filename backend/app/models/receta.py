from datetime import date

from sqlalchemy import Date, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid


class Receta(Base):
    __tablename__ = "recetas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    consulta_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("consultas.id"), nullable=False, index=True
    )
    fecha_emision: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=False)

    consulta: Mapped["Consulta"] = relationship("Consulta", back_populates="recetas")  # noqa: F821
    medicamentos: Mapped[list["MedicamentoReceta"]] = relationship(  # noqa: F821
        "MedicamentoReceta", back_populates="receta"
    )
