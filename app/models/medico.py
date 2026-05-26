from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid


class Medico(Base, TimestampMixin):
    __tablename__ = "medicos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    usuario_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("usuarios.id"), unique=True, nullable=False
    )
    especialidad: Mapped[str] = mapped_column(String(100), nullable=False)
    num_colegiado: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="medico")  # noqa: F821
    citas: Mapped[list["Cita"]] = relationship("Cita", back_populates="medico")  # noqa: F821
