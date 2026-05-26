import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import get_db
from app.main import app

# NullPool evita errores de event-loop cuando pytest-asyncio crea un nuevo loop por prueba.
_test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
_TestSession = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _override_get_db():
    async with _TestSession() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def admin_token(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@sece.local", "password": "Admin1234!"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(admin_token: str):
    return {"Authorization": f"Bearer {admin_token}"}


_MEDICO_COLEGIADO = "TEST0001"
_MEDICO_EMAIL = "medico.test@example.com"
_MEDICO_PASSWORD = "Medico1234!"


@pytest.fixture
async def medico_id(client: AsyncClient, admin_token: str) -> str:
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = await client.post(
        "/api/v1/medicos",
        json={
            "nombre": "Dr. Test",
            "especialidad": "General",
            "num_colegiado": _MEDICO_COLEGIADO,
            "email": _MEDICO_EMAIL,
            "password": _MEDICO_PASSWORD,
        },
        headers=headers,
    )
    if resp.status_code == 201:
        return resp.json()["id"]
    list_resp = await client.get("/api/v1/medicos", headers=headers)
    assert list_resp.status_code == 200
    for m in list_resp.json():
        if m["num_colegiado"] == _MEDICO_COLEGIADO:
            return m["id"]
    pytest.fail("No se pudo crear ni encontrar el médico de prueba")


@pytest.fixture
async def medico_token(client: AsyncClient, medico_id: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": _MEDICO_EMAIL, "password": _MEDICO_PASSWORD},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def medico_auth_headers(medico_token: str) -> dict:
    return {"Authorization": f"Bearer {medico_token}"}
