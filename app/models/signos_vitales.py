from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid


class SignosVitales(Base):
    __tablename__ = "signos_vitales"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    consulta_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("consultas.id"), unique=True, nullable=False
    )
    presion_arterial: Mapped[str | None] = mapped_column(String(20), nullable=True)
    temperatura: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)
    frecuencia_cardiaca: Mapped[int | None] = mapped_column(Integer, nullable=True)
    peso: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    talla: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    imc: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    consulta: Mapped["Consulta"] = relationship("Consulta", back_populates="signos_vitales")  # noqa: F821
