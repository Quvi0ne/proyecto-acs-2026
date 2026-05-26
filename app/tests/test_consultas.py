import time

import pytest
from httpx import AsyncClient

_TS = int(time.time())

_consulta_id: str | None = None
_paciente_id: str | None = None


async def _crear_cita(client, auth_headers, medico_id) -> dict:
    _dpi = str(time.time_ns() % 10_000_000_000_000).zfill(13)
    _hora = f"{_TS % 24:02d}:{_TS % 60:02d}:00"
    _fecha = f"2099-05-{(_TS % 27 + 1):02d}T{_hora}+00:00"

    pac = await client.post(
        "/api/v1/pacientes",
        json={"nombre_completo": "Consulta Test", "dpi": _dpi, "fecha_nacimiento": "1990-06-15", "sexo": "M"},
        headers=auth_headers,
    )
    assert pac.status_code == 201

    cita = await client.post(
        "/api/v1/citas",
        json={"paciente_id": pac.json()["id"], "medico_id": medico_id, "fecha_hora": _fecha},
        headers=auth_headers,
    )
    assert cita.status_code == 201
    return {"cita": cita.json(), "paciente": pac.json()}


@pytest.mark.asyncio
async def test_crear_consulta_y_cita_completa(
    client: AsyncClient, auth_headers: dict, medico_auth_headers: dict, medico_id: str
):
    global _consulta_id, _paciente_id
    data = await _crear_cita(client, auth_headers, medico_id)
    cita_id = data["cita"]["id"]
    _paciente_id = data["paciente"]["id"]

    resp = await client.post(
        "/api/v1/consultas",
        json={
            "cita_id": cita_id,
            "diagnostico": "Resfriado común",
            "notas_clinicas": "Paciente con tos leve",
        },
        headers=medico_auth_headers,
    )
    assert resp.status_code == 201
    _consulta_id = resp.json()["id"]

    # La cita debe quedar COMPLETADA
    cita_resp = await client.get(f"/api/v1/citas/{cita_id}", headers=auth_headers)
    assert cita_resp.json()["estado"] == "COMPLETADA"


@pytest.mark.asyncio
async def test_consulta_duplicada_rechazada(
    client: AsyncClient, auth_headers: dict, medico_auth_headers: dict, medico_id: str
):
    assert _consulta_id is not None, "test_crear_consulta_y_cita_completa debe ejecutarse primero"
    # Obtener el cita_id de la consulta ya creada
    consulta_resp = await client.get(f"/api/v1/consultas/{_consulta_id}", headers=medico_auth_headers)
    cita_id = consulta_resp.json()["cita_id"]

    resp = await client.post(
        "/api/v1/consultas",
        json={"cita_id": cita_id, "diagnostico": "intento duplicado"},
        headers=medico_auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_signos_vitales_calcula_imc(
    client: AsyncClient, auth_headers: dict, medico_auth_headers: dict, medico_id: str
):
    assert _consulta_id is not None, "test_crear_consulta_y_cita_completa debe ejecutarse primero"

    resp = await client.post(
        f"/api/v1/consultas/{_consulta_id}/signos-vitales",
        json={
            "presion_arterial": "120/80",
            "temperatura": 36.5,
            "frecuencia_cardiaca": 72,
            "peso": 70.0,
            "talla": 1.70,
        },
        headers=medico_auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["presion_arterial"] == "120/80"
    imc = float(data["imc"])
    assert abs(imc - 24.22) < 0.1


@pytest.mark.asyncio
async def test_historial_consultas_paciente(
    client: AsyncClient, auth_headers: dict
):
    assert _paciente_id is not None, "test_crear_consulta_y_cita_completa debe ejecutarse primero"

    resp = await client.get(f"/api/v1/pacientes/{_paciente_id}/consultas", headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert results[0]["diagnostico"] == "Resfriado común"


@pytest.mark.asyncio
async def test_consultas_solo_medico(client: AsyncClient, auth_headers: dict):
    resp = await client.post("/api/v1/consultas", json={}, headers=auth_headers)
    assert resp.status_code == 403
