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
async def test_cancelar_cita(client: AsyncClient, auth_headers: dict, medico_id: str):
    _dpi = str(time.time_ns() % 10_000_000_000_000).zfill(13)
    _hora = f"{_TS % 24:02d}:{(_TS + 1) % 60:02d}:00"
    _fecha = f"2099-02-{(_TS % 27 + 1):02d}T{_hora}+00:00"

    pac = await client.post(
        "/api/v1/pacientes",
        json={"nombre_completo": "Cancel Test", "dpi": _dpi, "fecha_nacimiento": "1990-01-01", "sexo": "M"},
        headers=auth_headers,
    )
    assert pac.status_code == 201

    cita = await client.post(
        "/api/v1/citas",
        json={"paciente_id": pac.json()["id"], "medico_id": medico_id, "fecha_hora": _fecha},
        headers=auth_headers,
    )
    assert cita.status_code == 201
    cita_id = cita.json()["id"]

    resp = await client.patch(
        f"/api/v1/citas/{cita_id}",
        json={"estado": "CANCELADA", "motivo": "Paciente no disponible"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "CANCELADA"


@pytest.mark.asyncio
async def test_patch_cancelada_rechazado(client: AsyncClient, auth_headers: dict, medico_id: str):
    _dpi = str(time.time_ns() % 10_000_000_000_000).zfill(13)
    _hora = f"{_TS % 24:02d}:{(_TS + 2) % 60:02d}:00"
    _fecha = f"2099-03-{(_TS % 27 + 1):02d}T{_hora}+00:00"

    pac = await client.post(
        "/api/v1/pacientes",
        json={"nombre_completo": "Patch Reject Test", "dpi": _dpi, "fecha_nacimiento": "1995-05-05", "sexo": "F"},
        headers=auth_headers,
    )
    cita = await client.post(
        "/api/v1/citas",
        json={"paciente_id": pac.json()["id"], "medico_id": medico_id, "fecha_hora": _fecha},
        headers=auth_headers,
    )
    cita_id = cita.json()["id"]

    # Cancelar la cita primero
    await client.patch(f"/api/v1/citas/{cita_id}", json={"estado": "CANCELADA"}, headers=auth_headers)

    # Intentar modificar la cita cancelada — debe retornar 422
    resp = await client.patch(f"/api/v1/citas/{cita_id}", json={"motivo": "intento tardío"}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reprogramar_cita(client: AsyncClient, auth_headers: dict, medico_id: str):
    _dpi = str(time.time_ns() % 10_000_000_000_000).zfill(13)
    _hora = f"{_TS % 24:02d}:{(_TS + 3) % 60:02d}:00"
    _fecha_orig = f"2099-04-{(_TS % 27 + 1):02d}T{_hora}+00:00"
    _hora2 = f"{(_TS + 1) % 24:02d}:{(_TS + 3) % 60:02d}:00"
    _fecha_nueva = f"2099-04-{(_TS % 27 + 2):02d}T{_hora2}+00:00"

    pac = await client.post(
        "/api/v1/pacientes",
        json={"nombre_completo": "Reprog Test", "dpi": _dpi, "fecha_nacimiento": "1988-12-01", "sexo": "M"},
        headers=auth_headers,
    )
    cita = await client.post(
        "/api/v1/citas",
        json={"paciente_id": pac.json()["id"], "medico_id": medico_id, "fecha_hora": _fecha_orig},
        headers=auth_headers,
    )
    assert cita.status_code == 201
    cita_id = cita.json()["id"]

    resp = await client.patch(
        f"/api/v1/citas/{cita_id}",
        json={"fecha_hora": _fecha_nueva},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["fecha_hora"].startswith(_fecha_nueva[:16])


@pytest.mark.asyncio
async def test_create_cita_requiere_auth(client: AsyncClient):
    resp = await client.post("/api/v1/citas", json={})
    assert resp.status_code in (401, 403)
