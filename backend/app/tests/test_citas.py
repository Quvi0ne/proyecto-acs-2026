import time

import pytest
from httpx import AsyncClient

_TS = int(time.time())
_DPI_CITA = str(_TS % 10_000_000_000_000).zfill(13)
# Fecha única por corrida para evitar conflictos con ejecuciones anteriores
_HORA = f"{_TS % 24:02d}:{_TS % 60:02d}:00"
_FECHA_CONFLICTO = f"2099-01-{(_TS % 27 + 1):02d}T{_HORA}+00:00"

_paciente_id: str | None = None
_cita_id: str | None = None


@pytest.mark.asyncio
async def test_create_cita_ok(client: AsyncClient, auth_headers: dict, medico_id: str):
    global _paciente_id, _cita_id
    resp = await client.post(
        "/api/v1/pacientes",
        json={
            "nombre_completo": "Paciente Test Citas",
            "dpi": _DPI_CITA,
            "fecha_nacimiento": "1985-05-20",
            "sexo": "F",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    _paciente_id = resp.json()["id"]

    resp = await client.post(
        "/api/v1/citas",
        json={
            "paciente_id": _paciente_id,
            "medico_id": medico_id,
            "fecha_hora": _FECHA_CONFLICTO,
            "motivo": "Revisión general",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["estado"] == "PROGRAMADA"
    assert data["paciente_id"] == _paciente_id
    assert data["medico_id"] == medico_id
    _cita_id = data["id"]


@pytest.mark.asyncio
async def test_create_cita_conflicto(client: AsyncClient, auth_headers: dict, medico_id: str):
    assert _paciente_id is not None, "test_create_cita_ok debe ejecutarse primero"
    resp = await client.post(
        "/api/v1/citas",
        json={
            "paciente_id": _paciente_id,
            "medico_id": medico_id,
            "fecha_hora": _FECHA_CONFLICTO,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_cita(client: AsyncClient, auth_headers: dict):
    assert _cita_id is not None, "test_create_cita_ok debe ejecutarse primero"
    resp = await client.get(f"/api/v1/citas/{_cita_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == _cita_id


@pytest.mark.asyncio
async def test_create_cita_requiere_auth(client: AsyncClient):
    resp = await client.post("/api/v1/citas", json={})
    assert resp.status_code in (401, 403)
