import enum


class Rol(str, enum.Enum):
    ADMIN = "ADMIN"
    MEDICO = "MEDICO"
    RECEPCIONISTA = "RECEPCIONISTA"


class EstadoCita(str, enum.Enum):
    PROGRAMADA = "PROGRAMADA"
    CANCELADA = "CANCELADA"
    COMPLETADA = "COMPLETADA"


class Sexo(str, enum.Enum):
    M = "M"
    F = "F"
