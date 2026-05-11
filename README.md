# SECE — Sistema de Expediente Clínico Electrónico

FastAPI · SQLAlchemy 2.0 async · PostgreSQL 15 · Alembic · JWT + bcrypt

## Configuración

```bash
# Instalar dependencias
uv sync

# Aplicar migraciones (PostgreSQL debe estar en ejecución)
uv run alembic upgrade head

# Crear usuario administrador inicial
uv run python -m app.scripts.seed_admin

# Iniciar servidor de desarrollo
uv run uvicorn app.main:app --reload
```

API: http://localhost:8000  
Swagger: http://localhost:8000/docs

## Pruebas

```bash
uv run pytest
```

## Variables de entorno

Copia `.env.example` a `.env`:

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Cadena de conexión asyncpg para PostgreSQL |
| `JWT_SECRET` | Clave para firmar los tokens JWT |
| `JWT_EXPIRE_MINUTES` | Expiración del token (por defecto 60) |
| `ADMIN_EMAIL` | Correo del administrador inicial (script de seed) |
| `ADMIN_PASSWORD` | Contraseña del administrador inicial (script de seed) |

## Arquitectura

```
app/
├── main.py          Punto de entrada de la aplicación FastAPI
├── core/            Configuración, sesión de BD, JWT/bcrypt y dependencias de rol
├── models/          Modelos ORM con SQLAlchemy 2.0
├── schemas/         Esquemas Pydantic v2 para peticiones y respuestas
├── repositories/    Capa de acceso a datos asíncrona
├── api/v1/          Routers de FastAPI (uno por dominio)
├── web/             Vistas HTML renderizadas con Jinja2
├── scripts/         Utilidades de línea de comandos
└── tests/           Suite de pruebas con pytest
```
