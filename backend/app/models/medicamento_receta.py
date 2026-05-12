from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid


class MedicamentoReceta(Base):
    __tablename__ = "medicamentos_receta"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    receta_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("recetas.id"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    dosis: Mapped[str | None] = mapped_column(String(50), nullable=True)
    via: Mapped[str | None] = mapped_column(String(50), nullable=True)
    frecuencia: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duracion: Mapped[str | None] = mapped_column(String(50), nullable=True)

    receta: Mapped["Receta"] = relationship("Receta", back_populates="medicamentos")  # noqa: F821
