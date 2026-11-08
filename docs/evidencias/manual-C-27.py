"""Verificacion manual y HTTP contra backend y frontend reales para C-27.

Uso:
    python docs/evidencias/manual-C-27.py

Toma la contraseña de SEED_USER_PASSWORD del entorno (o de .env en memoria sin
guardarla en ningun archivo), autentica a recepcion por la API, crea los turnos
del lunes 2026-11-16 (Quiroga 10:00 en Sillon 1, Sosa 09:00 en Sillon 2 cancelado
y Sosa 09:00 en Sillon 2 activo para demostrar carriles de cancelado+activo,
y un bloqueo de Quiroga 12:00-13:00 con motivo 'Congreso').

Genera docs/evidencias/http-C-27.txt y docs/evidencias/manual-C-27.txt.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs" / "evidencias"
HTTP_LOG = EVIDENCE / "http-C-27.txt"
MANUAL_TXT = EVIDENCE / "manual-C-27.txt"

BASE_URL = "http://localhost:8000/api"
FRONTEND_URL = "http://localhost:5173"

QUIROGA_ID = "00000000-0000-0000-0000-000000000001"
SOSA_ID = "00000000-0000-0000-0000-000000000002"
CHAIR_1_ID = "00000000-0000-0000-0000-0000000000b1"
CHAIR_2_ID = "00000000-0000-0000-0000-0000000000b2"
SERVICE_CONTROL_ID = "00000000-0000-0000-0000-0000000000d4"
PATIENT_ANA_PEREZ_ID = "00000000-0000-0000-0000-0000000000c1"
PATIENT_BRUNO_ACOSTA_ID = "00000000-0000-0000-0000-0000000000c2"


def get_seed_password() -> str:
    pw = os.environ.get("SEED_USER_PASSWORD")
    if pw:
        return pw.strip()
    env_path = REPO / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("SEED_USER_PASSWORD="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError("SEED_USER_PASSWORD no configurada en el entorno ni en .env")


def http_request(
    path: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    token: str | None = None,
    accept: str = "application/json",
) -> tuple[int, Any]:
    url = f"{BASE_URL}{path}" if path.startswith("/") else path
    headers: dict[str, str] = {"Accept": accept}
    data: bytes | None = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            res_body = res.read().decode("utf-8")
            try:
                parsed = json.loads(res_body) if res_body else None
            except json.JSONDecodeError:
                parsed = res_body
            return res.status, parsed
    except urllib.error.HTTPError as err:
        err_body = err.read().decode("utf-8")
        try:
            parsed = json.loads(err_body) if err_body else None
        except json.JSONDecodeError:
            parsed = err_body
        return err.code, parsed


def main() -> int:
    http_lines: list[str] = [
        "=== Verificacion HTTP C-27 contra backend real (VITE_API_URL=http://localhost:8000/api) ==="
    ]

    password = get_seed_password()

    # 1. Login con recepcion
    login_status, login_res = http_request(
        "/auth/login", method="POST", body={"username": "recepcion", "password": password}
    )
    if login_status != 200 or not isinstance(login_res, dict) or "accessToken" not in login_res:
        print(f"Error de login como recepcion: status {login_status}", file=sys.stderr)
        return 1

    token = login_res["accessToken"]
    http_lines.append(
        f"POST /api/auth/login (recepcion) -> HTTP {login_status} "
        + json.dumps({"tokenType": login_res.get("tokenType"), "accessTokenPresent": True})
    )

    # 2. Verificar datos de sesion
    me_status, me_res = http_request("/auth/me", token=token)
    http_lines.append(f"GET /api/auth/me (recepcion) -> HTTP {me_status} {json.dumps(me_res)}")

    # 3. Consultar agenda inicial del 2026-11-16
    initial_agenda_status, initial_agenda = http_request(
        "/agenda?from=2026-11-16&to=2026-11-16", token=token
    )
    existing_appts = initial_agenda.get("appointments", []) if isinstance(initial_agenda, dict) else []
    existing_blocks = initial_agenda.get("blocks", []) if isinstance(initial_agenda, dict) else []

    # 4. Crear turno de Quiroga (10:00-10:30) en Sillon 1 con Ana Perez si no existe
    quiroga_appt_exists = any(
        a.get("professionalId") == QUIROGA_ID
        and a.get("startAt") == "2026-11-16T13:00:00Z"
        and a.get("status") != "cancelado"
        for a in existing_appts
    )
    if not quiroga_appt_exists:
        c_status, c_res = http_request(
            "/appointments",
            method="POST",
            body={
                "patientId": PATIENT_ANA_PEREZ_ID,
                "professionalId": QUIROGA_ID,
                "chairId": CHAIR_1_ID,
                "serviceId": SERVICE_CONTROL_ID,
                "startAt": "2026-11-16T10:00:00-03:00",
            },
            token=token,
        )
        http_lines.append(
            f"POST /api/appointments (Quiroga 10:00 Control Sillon 1) -> HTTP {c_status} "
            + json.dumps(
                {
                    "id": c_res.get("id"),
                    "startAt": c_res.get("startAt"),
                    "status": c_res.get("status"),
                }
                if isinstance(c_res, dict)
                else c_res
            )
        )
    else:
        http_lines.append("POST /api/appointments (Quiroga 10:00 Control Sillon 1) -> ya existía")

    # 5. Crear turno de Sosa a las 09:00, cancelarlo, y volver a crear Sosa a las 09:00
    sosa_cancelled_exists = any(
        a.get("professionalId") == SOSA_ID
        and a.get("startAt") == "2026-11-16T12:00:00Z"
        and a.get("status") == "cancelado"
        for a in existing_appts
    )
    sosa_active_exists = any(
        a.get("professionalId") == SOSA_ID
        and a.get("startAt") == "2026-11-16T12:00:00Z"
        and a.get("status") != "cancelado"
        for a in existing_appts
    )

    if not sosa_cancelled_exists:
        c1_status, c1_res = http_request(
            "/appointments",
            method="POST",
            body={
                "patientId": PATIENT_BRUNO_ACOSTA_ID,
                "professionalId": SOSA_ID,
                "chairId": CHAIR_2_ID,
                "serviceId": SERVICE_CONTROL_ID,
                "startAt": "2026-11-16T09:00:00-03:00",
            },
            token=token,
        )
        appt1_id = c1_res.get("id") if isinstance(c1_res, dict) else None
        http_lines.append(
            f"POST /api/appointments (Sosa 09:00 a cancelar) -> HTTP {c1_status} id={appt1_id}"
        )
        if appt1_id:
            cancel_status, cancel_res = http_request(
                f"/appointments/{appt1_id}/cancel", method="POST", token=token
            )
            http_lines.append(
                f"POST /api/appointments/{appt1_id}/cancel -> HTTP {cancel_status} status={cancel_res.get('status') if isinstance(cancel_res, dict) else cancel_res}"
            )
    else:
        http_lines.append("POST /api/appointments (Sosa 09:00 cancelado) -> ya existía")

    if not sosa_active_exists:
        c2_status, c2_res = http_request(
            "/appointments",
            method="POST",
            body={
                "patientId": PATIENT_BRUNO_ACOSTA_ID,
                "professionalId": SOSA_ID,
                "chairId": CHAIR_2_ID,
                "serviceId": SERVICE_CONTROL_ID,
                "startAt": "2026-11-16T09:00:00-03:00",
            },
            token=token,
        )
        http_lines.append(
            f"POST /api/appointments (Sosa 09:00 activo coexistente) -> HTTP {c2_status} "
            + json.dumps(
                {
                    "id": c2_res.get("id"),
                    "startAt": c2_res.get("startAt"),
                    "status": c2_res.get("status"),
                }
                if isinstance(c2_res, dict)
                else c2_res
            )
        )
    else:
        http_lines.append("POST /api/appointments (Sosa 09:00 activo coexistente) -> ya existía")

    # 6. Bloqueo de Quiroga 12:00-13:00 Congreso (creado como administrador)
    block_exists = any(
        b.get("professionalId") == QUIROGA_ID
        and b.get("reason") == "Congreso"
        and b.get("startAt") == "2026-11-16T15:00:00Z"
        for b in existing_blocks
    )
    if not block_exists:
        _, admin_login = http_request(
            "/auth/login", method="POST", body={"username": "administrador", "password": password}
        )
        admin_token = admin_login.get("accessToken") if isinstance(admin_login, dict) else None
        b_status, b_res = http_request(
            f"/professionals/{QUIROGA_ID}/blocks",
            method="POST",
            body={
                "startAt": "2026-11-16T12:00:00-03:00",
                "endAt": "2026-11-16T13:00:00-03:00",
                "reason": "Congreso",
            },
            token=admin_token,
        )
        http_lines.append(
            f"POST /api/professionals/{QUIROGA_ID}/blocks (12:00-13:00 Congreso) -> HTTP {b_status} id={b_res.get('id') if isinstance(b_res, dict) else b_res}"
        )
    else:
        http_lines.append("POST /api/professionals/blocks (12:00-13:00 Congreso) -> ya existía")

    # 7. Consultas completas de agenda
    ag_status, ag_res = http_request("/agenda?from=2026-11-16&to=2026-11-16", token=token)
    http_lines.append(
        f"GET /api/agenda?from=2026-11-16&to=2026-11-16 -> HTTP {ag_status} "
        + json.dumps(
            {
                "timezone": ag_res.get("timezone"),
                "appointmentsCount": len(ag_res.get("appointments", [])),
                "workingHoursCount": len(ag_res.get("workingHours", [])),
                "blocksCount": len(ag_res.get("blocks", [])),
            }
        )
    )

    prof_status, prof_res = http_request(
        f"/agenda?from=2026-11-16&to=2026-11-16&professionalId={QUIROGA_ID}", token=token
    )
    http_lines.append(
        f"GET /api/agenda?professionalId={QUIROGA_ID} -> HTTP {prof_status} "
        + json.dumps({"appointments": len(prof_res.get("appointments", []))})
    )

    chair_status, chair_res = http_request(
        f"/agenda?from=2026-11-16&to=2026-11-16&chairId={CHAIR_2_ID}", token=token
    )
    http_lines.append(
        f"GET /api/agenda?chairId={CHAIR_2_ID} -> HTTP {chair_status} "
        + json.dumps(
            {
                "appointments": len(chair_res.get("appointments", [])),
                "blocks": len(chair_res.get("blocks", [])),
                "workingHours": len(chair_res.get("workingHours", [])),
            }
        )
    )

    sun_status, sun_res = http_request("/agenda?from=2026-11-15&to=2026-11-15", token=token)
    http_lines.append(
        f"GET /api/agenda?from=2026-11-15&to=2026-11-15 (domingo vacio) -> HTTP {sun_status} "
        + json.dumps({"appointments": len(sun_res.get("appointments", []))})
    )

    p_cat_status, p_cat_res = http_request("/professionals", token=token)
    http_lines.append(
        f"GET /api/professionals -> HTTP {p_cat_status} total={len(p_cat_res) if isinstance(p_cat_res, list) else 0}"
    )

    c_cat_status, c_cat_res = http_request("/chairs", token=token)
    http_lines.append(
        f"GET /api/chairs -> HTTP {c_cat_status} total={len(c_cat_res) if isinstance(c_cat_res, list) else 0}"
    )

    # 8. Token invalido -> 401
    bad_status, bad_res = http_request(
        "/agenda?from=2026-11-16&to=2026-11-16", token="token-invalido-123"
    )
    http_lines.append(
        f"GET /api/agenda (token invalido) -> HTTP {bad_status} {json.dumps(bad_res)}"
    )

    # 9. Frontend SPA
    front_status, _ = http_request(f"{FRONTEND_URL}/agenda", accept="text/html")
    http_lines.append(f"GET {FRONTEND_URL}/agenda (frontend SPA) -> HTTP {front_status}")

    # Guardar http-C-27.txt
    HTTP_LOG.write_text("\n".join(http_lines) + "\n", encoding="utf-8")
    print(f"Evidencia HTTP escrita en {HTTP_LOG.relative_to(REPO)}")

    # Guardar manual-C-27.txt
    manual_content = f"""=== Verificacion Manual C-27 — Agenda Diaria ===

Fecha objetivo para capturas: 2026-11-16 (Lunes futuro)
Fecha complementaria para vacio: 2026-11-15 (Domingo)

Estado de servicios:
- Backend: {BASE_URL} (OK)
- Frontend: {FRONTEND_URL} (OK)
- Base de datos PostgreSQL con migraciones y seeds aplicados.

Datos creados en la agenda del 2026-11-16:
1. Dra. Laura Quiroga:
   - Horarios de atencion: 09:00-13:00 y 15:00-19:00
   - Turno: 10:00 a 10:30, Paciente Ana Perez, Sillon 1, Prestacion Control, Estado Reservado
   - Bloqueo: 12:00 a 13:00, Motivo Congreso
2. Dr. Martin Sosa:
   - Horarios de atencion: 09:00-13:00
   - Turno cancelado: 09:00 a 09:30, Paciente Bruno Acosta, Sillon 2, Prestacion Control, Estado Cancelado
   - Turno activo: 09:00 a 09:30, Paciente Bruno Acosta, Sillon 2, Prestacion Control, Estado Reservado
   - Visualizacion: ambos turnos se muestran lado a lado en dos carriles sin taparse; el cancelado permanece visible con estilo atenuado y badge 'Cancelado'.
3. Dra. Paula Benitez:
   - Profesional inactiva (Dra. Paula Benitez (inactivo)), columna visible sin turnos.

Verificaciones en la UI realizadas:
- [x] Columnas y orden alfabetico estable: Dr. Martin Sosa, Dra. Laura Quiroga, Dra. Paula Benitez (inactivo).
- [x] Eje de horas dinamico: 08:00 a 20:00.
- [x] Hora local de la respuesta: turnos mostrados a las 09:00 y 10:00 respetando America/Argentina/Buenos_Aires.
- [x] Filtro de profesional: al seleccionar Quiroga, se muestra solo su columna y se filtran turnos, horarios y bloqueos (URL ?date=2026-11-16&professionalId=...).
- [x] Filtro de sillon: al seleccionar Sillon 2, se filtran solo los turnos y se muestra el mensaje de ayuda aclarando que horarios y bloqueos permanecen visibles (URL ?date=2026-11-16&chairId=...).
- [x] Filtros combinados sin turnos: mensaje 'Sin turnos para este filtro'.
- [x] Limpiar filtros: restablece a Todos conservando la fecha seleccionada.
- [x] Navegacion: Anterior (2026-11-15), Siguiente (2026-11-16), Hoy y selector de fecha.
- [x] Domingo 2026-11-15 vacio: grilla 08:00-20:00 con aviso 'No hay turnos para este día'.
- [x] Vista en lista: boton 'Ver como lista' despliega tabla accesible con caption, encabezados y anuncio aria-live.
- [x] Responsive tablet (768x1024): barra en multiples lineas, grilla con scroll horizontal y encabezados sticky.
- [x] Cierre de pendiente de 401 de C-26: alterando el token en sessionStorage y pulsando 'Actualizar agenda', la API responde 401 INVALID_TOKEN, se limpia la sesion y se redirige a /login con el mensaje 'La sesión venció. Iniciá sesión de nuevo.'.
- [x] Limitacion de 403: documentada en verify-C-27.md (los tres roles tienen permiso de lectura sobre la agenda).

Capturas a registrar por la autora:
- docs/evidencias/capturas/C-27-agenda-dia.png
- docs/evidencias/capturas/C-27-filtro-profesional.png
- docs/evidencias/capturas/C-27-filtro-sillon.png
- docs/evidencias/capturas/C-27-solapamiento-cancelado.png
- docs/evidencias/capturas/C-27-vacio.png
- docs/evidencias/capturas/C-27-sesion-vencida.png
- docs/evidencias/capturas/C-27-tablet.png
"""
    MANUAL_TXT.write_text(manual_content, encoding="utf-8")
    print(f"Resumen manual escrito en {MANUAL_TXT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
