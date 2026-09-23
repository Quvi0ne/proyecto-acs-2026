import time

import pytest
from httpx import AsyncClient

_receta_id: str | None = None


async def _crear_consulta(client, auth_headers, medico_auth_headers, medico_id) -> str:
    dpi = str(time.time_ns() % 10_000_000_000_000).zfill(13)
    ts = int(time.time())
    fecha = f"2099-06-{(ts % 27 + 1):02d}T{ts % 24:02d}:{ts % 60:02d}:00+00:00"

    pac = await client.post(
        "/api/v1/pacientes",
        json={"nombre_completo": "Receta Test", "dpi": dpi, "fecha_nacimiento": "1985-03-10", "sexo": "F"},
        headers=auth_headers,
    )
    assert pac.status_code == 201

    cita = await client.post(
        "/api/v1/citas",
        json={"paciente_id": pac.json()["id"], "medico_id": medico_id, "fecha_hora": fecha},
        headers=auth_headers,
    )
    assert cita.status_code == 201

    consulta = await client.post(
        "/api/v1/consultas",
        json={"cita_id": cita.json()["id"], "diagnostico": "Hipertensión leve"},
        headers=medico_auth_headers,
    )
    assert consulta.status_code == 201
    return consulta.json()["id"]


@pytest.mark.asyncio
async def test_actualizar_consulta(
    client: AsyncClient, auth_headers: dict, medico_auth_headers: dict, medico_id: str
):
    consulta_id = await _crear_consulta(client, auth_headers, medico_auth_headers, medico_id)

    resp = await client.patch(
        f"/api/v1/consultas/{consulta_id}",
        json={"notas_clinicas": "Paciente refiere cefalea ocasional"},
        headers=medico_auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["notas_clinicas"] == "Paciente refiere cefalea ocasional"
    assert resp.json()["diagnostico"] == "Hipertensión leve"


@pytest.mark.asyncio
async def test_actualizar_consulta_no_existe(client: AsyncClient, medico_auth_headers: dict):
    resp = await client.patch(
        "/api/v1/consultas/00000000-0000-0000-0000-000000000000",
        json={"diagnostico": "Inexistente"},
        headers=medico_auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_emitir_receta(
    client: AsyncClient, auth_headers: dict, medico_auth_headers: dict, medico_id: str
):
    global _receta_id
    consulta_id = await _crear_consulta(client, auth_headers, medico_auth_headers, medico_id)

    resp = await client.post(
        f"/api/v1/consultas/{consulta_id}/recetas",
        json={
            "medicamentos": [
                {"nombre": "Losartán", "dosis": "50mg", "via": "oral", "frecuencia": "1 vez al día", "duracion": "30 días"},
                {"nombre": "Amlodipino", "dosis": "5mg", "via": "oral", "frecuencia": "1 vez al día"},
            ]
        },
        headers=medico_auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["consulta_id"] == consulta_id
    assert len(data["medicamentos"]) == 2
    nombres = [m["nombre"] for m in data["medicamentos"]]
    assert "Losartán" in nombres
    _receta_id = data["id"]


@pytest.mark.asyncio
async def test_receta_sin_medicamentos(
    client: AsyncClient, auth_headers: dict, medico_auth_headers: dict, medico_id: str
):
    consulta_id = await _crear_consulta(client, auth_headers, medico_auth_headers, medico_id)

    resp = await client.post(
        f"/api/v1/consultas/{consulta_id}/recetas",
        json={"medicamentos": []},
        headers=medico_auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_receta(client: AsyncClient, auth_headers: dict):
    assert _receta_id is not None, "test_emitir_receta debe ejecutarse primero"

    resp = await client.get(f"/api/v1/recetas/{_receta_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["medicamentos"]) == 2
    assert data["fecha_emision"] is not None


@pytest.mark.asyncio
async def test_receta_consulta_no_existe(client: AsyncClient, medico_auth_headers: dict):
    resp = await client.post(
        "/api/v1/consultas/00000000-0000-0000-0000-000000000000/recetas",
        json={"medicamentos": [{"nombre": "Prueba"}]},
        headers=medico_auth_headers,
    )
    assert resp.status_code == 404
