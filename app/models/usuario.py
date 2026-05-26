from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, new_uuid
from app.models.enums import Rol


class Usuario(Base, TimestampMixin):
    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[Rol] = mapped_column(Enum(Rol), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    medico: Mapped["Medico"] = relationship("Medico", back_populates="usuario", uselist=False)  # noqa: F821
