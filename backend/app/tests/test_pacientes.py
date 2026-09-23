import time

import pytest
from httpx import AsyncClient

# DPI único por sesión de prueba para evitar colisiones con datos existentes en la BD
_DPI = str(time.time_ns() % 10_000_000_000_000).zfill(13)

PACIENTE_BASE = {
    "nombre_completo": "Juan Pérez García",
    "dpi": _DPI,
    "fecha_nacimiento": "1990-03-15",
    "sexo": "M",
    "telefono": "5555-1234",
}


@pytest.mark.asyncio
async def test_create_paciente(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/pacientes", json=PACIENTE_BASE, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["dpi"] == PACIENTE_BASE["dpi"]
    assert data["codigo_expediente"].startswith("EXP-")


@pytest.mark.asyncio
async def test_create_paciente_duplicate_dpi(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/pacientes", json=PACIENTE_BASE, headers=auth_headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_search_paciente(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/pacientes?q=Juan", headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert any(p["dpi"] == PACIENTE_BASE["dpi"] for p in results)


@pytest.mark.asyncio
async def test_search_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/pacientes?q=test")
    assert resp.status_code in (401, 403)
