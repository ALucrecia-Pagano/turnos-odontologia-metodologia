"""Login de los tres roles y GET /api/auth/me contra la API en ejecucion.

Uso, desde backend/, con el contenedor levantado:

    API_URL=http://localhost:8000/api python ../docs/evidencias/e2e-C-19.py

Imprime solo status y rol: nunca el token ni la contrasena. Sale con codigo 0 solo si
los tres usuarios entran con su rol y la contrasena incorrecta recibe 401.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BACKEND = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND))

from app.config import load_settings  # noqa: E402

USERS = ("administrador", "recepcion", "odontologo")
WRONG_PASSWORD = "esta-no-es-la-clave"


def call(
    url: str, *, body: dict[str, str] | None = None, token: str | None = None
) -> tuple[int, dict[str, object]]:
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = Request(url, data=data, headers=headers)
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        return error.code, json.load(error)


def main() -> int:
    settings = load_settings()
    api_url = os.environ.get("API_URL", f"http://localhost:{settings.api_port}/api").rstrip("/")
    secret = settings.seed_user_password
    if secret is None:
        print("Falta SEED_USER_PASSWORD")
        return 2
    password = secret.get_secret_value()

    failures = 0
    for username in USERS:
        status, body = call(
            f"{api_url}/auth/login", body={"username": username, "password": password}
        )
        print(f"POST /auth/login {username}: status {status}")
        if status != 200:
            failures += 1
            continue
        status, me = call(f"{api_url}/auth/me", token=str(body["accessToken"]))
        role = me.get("role")
        print(f"GET /auth/me {username}: status {status}, rol {role}")
        if status != 200 or role != username:
            failures += 1

    status, _ = call(
        f"{api_url}/auth/login", body={"username": "recepcion", "password": WRONG_PASSWORD}
    )
    print(f"POST /auth/login recepcion con contrasena incorrecta: status {status}")
    if status != 401:
        failures += 1

    print(f"fallos: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
