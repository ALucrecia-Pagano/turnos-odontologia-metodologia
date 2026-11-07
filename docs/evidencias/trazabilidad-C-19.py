"""Trazabilidad de C-19: cada escenario de las dos specs delta a un test recolectado.

Uso, desde backend/:

    python ../docs/evidencias/trazabilidad-C-19.py

Lee los escenarios de las specs, comprueba con `pytest --collect-only` que cada test
existe, genera trazabilidad-C-19.txt y regenera la tabla de verify-C-19.md. Termina con
codigo 0 solo si no falta ningun escenario y no sobra ninguna fila.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
EVIDENCE = REPO / "docs" / "evidencias"
OUTPUT = EVIDENCE / "trazabilidad-C-19.txt"
VERIFY = EVIDENCE / "verify-C-19.md"
SPECS = (
    REPO
    / "openspec"
    / "changes"
    / "archive"
    / "2026-11-06-autenticacion-jwt-y-roles"
    / "specs"
)
AUTH_SPEC = SPECS / "authentication-and-rbac" / "spec.md"
INFRA_SPEC = SPECS / "database-infrastructure" / "spec.md"
TABLE_START = "<!-- trazabilidad:inicio -->"
TABLE_END = "<!-- trazabilidad:fin -->"

VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

LOGIN = "tests/integration/test_auth_login.py"
INPUT = "tests/api/test_login_input.py"
PASSWORDS = "tests/auth/test_passwords.py"
TOKENS = "tests/auth/test_tokens.py"
REJECTION = "tests/api/test_token_rejection.py"
CURRENT = "tests/integration/test_auth_current_user.py"
PERMISSIONS = "tests/auth/test_permissions.py"
MATRIX = "tests/integration/test_rbac_matrix.py"
PARITY = "tests/auth/test_rbac_domain_parity.py"
GUARDS = "tests/api/test_route_guards.py"
CONFIG = "tests/test_config.py"
LEAKS = "tests/integration/test_auth_no_leaks.py"
REPOSITORY = "tests/integration/test_user_repository.py"
MODEL = "tests/auth/test_model.py"
OPENAPI = "tests/api/test_auth_openapi.py"
PERSISTENCE = "tests/integration/test_user_persistence.py"
INFRA = "tests/integration/test_database_infrastructure.py"
SEED = "tests/integration/test_seed_users.py"

TRACE: dict[str, dict[str, dict[str, str]]] = {
    "authentication-and-rbac": {
        "Login con credenciales válidas": {
            "Login correcto del administrador": f"{LOGIN}::test_login_success[administrador]",
            "Login correcto de recepción": f"{LOGIN}::test_login_success[recepcion]",
            "Login correcto del odontólogo": f"{LOGIN}::test_login_success[odontologo]",
            "La respuesta del login no se guarda en caché": f"{LOGIN}::test_login_response_has_no_store",
            "El usuario se normaliza al buscarlo": f"{LOGIN}::test_login_normalizes_username",
        },
        "Mismo 401 ante credenciales inválidas": {
            "Contraseña incorrecta": f"{LOGIN}::test_wrong_password_is_rejected",
            "Usuario inexistente": f"{LOGIN}::test_unknown_user_is_rejected",
            "Usuario inactivo con contraseña correcta": f"{LOGIN}::test_inactive_user_with_correct_password_is_rejected",
            "Usuario inactivo con contraseña incorrecta": f"{LOGIN}::test_inactive_user_with_wrong_password_is_rejected",
            "Los cuerpos son idénticos byte por byte": f"{LOGIN}::test_invalid_credentials_are_byte_identical",
            "Un usuario inexistente se verifica contra el hash ficticio": f"{PASSWORDS}::test_missing_user_uses_dummy_hash",
            "Un hash guardado corrupto cuenta como contraseña incorrecta": f"{LOGIN}::test_corrupt_stored_hash_is_rejected",
        },
        "Entrada del login validada": {
            "Falta la contraseña": f"{INPUT}::test_missing_password_returns_400",
            "Contraseña de más de 128 caracteres": f"{INPUT}::test_too_long_password_returns_400",
            "Campo adicional": f"{INPUT}::test_extra_field_returns_400",
        },
        "Contraseñas guardadas solo como hash Argon2id": {
            "El hash usa los parámetros fijados": f"{PASSWORDS}::test_hash_uses_fixed_parameters",
            "Dos hashes de la misma contraseña difieren": f"{PASSWORDS}::test_same_password_hashes_differ",
            "Una contraseña correcta se verifica": f"{PASSWORDS}::test_correct_password_verifies",
            "Una contraseña incorrecta no se verifica": f"{PASSWORDS}::test_wrong_password_does_not_verify",
            "Se verifica con los parámetros guardados en el hash": f"{PASSWORDS}::test_verify_uses_parameters_in_hash",
            "El perfil barato no está en producción": f"{PASSWORDS}::test_cheapest_profile_not_in_production",
        },
        "Token firmado con exactamente tres claims": {
            "Claims exactos del token": f"{TOKENS}::test_token_has_exact_claims",
            "El token del login corresponde al usuario": f"{LOGIN}::test_login_token_matches_user",
        },
        "Token ausente y formato inválido responden 401": {
            "Sin header Authorization": f"{REJECTION}::test_rejected_token[no_header]",
            "Bearer vacío": f"{REJECTION}::test_rejected_token[empty_bearer]",
            "Esquema Basic": f"{REJECTION}::test_rejected_token[basic_scheme]",
            "Texto que no es un token": f"{REJECTION}::test_rejected_token[garbage]",
            "Token válido en la URL": f"{REJECTION}::test_rejected_token[token_in_url]",
        },
        "Token vencido responde 401": {
            "Token vencido hace años": f"{REJECTION}::test_rejected_token[expired_years]",
            "Token vencido hace un segundo": f"{REJECTION}::test_rejected_token[expired_one_second]",
            "Un token vencido no abre conexión con la base": f"{REJECTION}::test_expired_token_does_not_open_database_connection",
        },
        "Token alterado responde 401": {
            "Payload cambiado con la firma original": f"{REJECTION}::test_rejected_token[tampered_payload]",
            "Firma alterada": f"{REJECTION}::test_rejected_token[tampered_signature]",
            "Firmado con otra clave": f"{REJECTION}::test_rejected_token[other_key]",
            "Algoritmo none": f"{REJECTION}::test_rejected_token[alg_none]",
            "Otro algoritmo con la misma clave": f"{REJECTION}::test_rejected_token[other_algorithm]",
            "Sin claim exp": f"{REJECTION}::test_rejected_token[missing_exp]",
            "Sin claim sub": f"{REJECTION}::test_rejected_token[missing_sub]",
            "Sin claim role": f"{REJECTION}::test_rejected_token[missing_role]",
            "Claim sub que no es un UUID": f"{REJECTION}::test_rejected_token[sub_not_uuid]",
            "Claim role desconocido": f"{REJECTION}::test_rejected_token[unknown_role]",
        },
        "El usuario se confirma contra la base en cada request": {
            "Usuario inexistente con token válido": f"{CURRENT}::test_unknown_user_with_valid_token_is_rejected",
            "Usuario desactivado con token vigente": f"{CURRENT}::test_deactivated_user_with_valid_token_is_rejected",
            "Usuario con otro rol y token vigente": f"{CURRENT}::test_role_changed_user_with_valid_token_is_rejected",
            "Después de cambiar el rol, un login nuevo trae el rol nuevo": f"{CURRENT}::test_new_login_after_role_change_has_new_role",
            "Usuario reactivado con token todavía vigente": f"{CURRENT}::test_reactivated_user_with_valid_token_is_accepted",
            "Cambio de profesional con token vigente": f"{CURRENT}::test_professional_change_with_valid_token_is_accepted",
        },
        "Datos del usuario autenticado": {
            "Usuario autenticado odontólogo": f"{CURRENT}::test_me_for_doctor",
            "Usuario autenticado de recepción": f"{CURRENT}::test_me_for_reception",
            "Usuario autenticado administrador": f"{CURRENT}::test_me_for_admin",
        },
        "Odontólogo con profesional desactivado": {
            "Login con el profesional desactivado": f"{CURRENT}::test_login_with_inactive_professional",
            "Consulta con el profesional desactivado": f"{CURRENT}::test_me_with_inactive_professional",
        },
        "Actor del dominio desde el usuario autenticado": {
            "Actor del odontólogo": f"{CURRENT}::test_actor_for_doctor",
            "Actor de recepción": f"{CURRENT}::test_actor_for_reception",
            "Actor del administrador": f"{CURRENT}::test_actor_for_admin",
            "Un header del cliente no cambia el Actor": f"{CURRENT}::test_client_header_does_not_change_actor",
        },
        "Matriz RBAC completa": {
            "La tabla de permisos coincide con la matriz": f"{PERMISSIONS}::test_permissions_match_literal_matrix",
            "La tabla de permisos cubre todas las combinaciones": f"{PERMISSIONS}::test_no_combination_is_missing",
            "Una combinación faltante se detecta": f"{PERMISSIONS}::test_missing_combination_is_detected",
            "Las 102 celdas responden lo esperado por HTTP": f"{MATRIX}::test_matrix_cell_over_http",
        },
        "Rol sin permiso responde 403 con violaciones": {
            "Odontólogo que da un turno": f"{MATRIX}::test_doctor_cannot_book",
            "Recepción que crea un profesional": f"{MATRIX}::test_reception_cannot_create_professional",
            "Nadie borra pacientes": f"{MATRIX}::test_nobody_deletes_patients",
            "Sin token en una ruta con permiso": f"{REJECTION}::test_no_token_on_permission_route",
        },
        "Alcance propio informado a la ruta": {
            "Odontólogo con alcance propio en horarios": f"{MATRIX}::test_doctor_scope_own_on_working_hours",
            "Administrador con alcance total en horarios": f"{MATRIX}::test_admin_scope_all_on_working_hours",
            "Odontólogo con alcance total en la agenda": f"{MATRIX}::test_doctor_scope_all_on_agenda",
        },
        "La matriz coincide con el dominio en los turnos": {
            "Paridad al reprogramar": f"{PARITY}::test_parity_reschedule",
            "Paridad al cancelar": f"{PARITY}::test_parity_cancel",
            "Paridad al cambiar estado de un turno propio": f"{PARITY}::test_parity_change_status_own",
            "Paridad al cambiar estado de un turno ajeno": f"{PARITY}::test_parity_change_status_foreign",
        },
        "Rechazo por defecto en todas las rutas": {
            "Salud sin token": f"{CURRENT}::test_health_without_token",
            "Las rutas reales no públicas exigen token": f"{GUARDS}::test_real_non_public_routes_require_token",
            "Una ruta sin protección se detecta": f"{GUARDS}::test_route_without_protection_is_detected",
            "Las rutas protegidas reales declaran permiso": f"{GUARDS}::test_real_protected_routes_declare_permission",
            "Una ruta protegida sin permiso se detecta": f"{GUARDS}::test_protected_route_without_permission_is_detected",
        },
        "Configuración del token validada al arrancar": {
            "Secreto de 31 caracteres": f"{CONFIG}::test_short_secret_error_hides_value",
            "Secreto de 32 caracteres": f"{CONFIG}::test_secret_of_32_characters_loads",
            "Secreto vacío": f"{CONFIG}::test_empty_secret_names_variable",
            "Algoritmo none": f"{CONFIG}::test_algorithm_none_is_rejected",
            "Algoritmo asimétrico": f"{CONFIG}::test_asymmetric_algorithm_is_rejected",
            "Vigencia en cero": f"{CONFIG}::test_zero_expiration_is_rejected",
        },
        "Secretos fuera de respuestas": {
            "El login no devuelve hash ni contraseña": f"{LEAKS}::test_login_response_has_no_secrets",
            "La consulta del usuario no devuelve hash": f"{LEAKS}::test_me_response_has_no_secrets",
            "Un login malformado no devuelve la contraseña": f"{INPUT}::test_malformed_login_does_not_return_password",
            "Los esquemas de respuesta no tienen hash": f"{INPUT}::test_response_schemas_have_no_hash",
        },
        "Secretos fuera de logs y mensajes de error": {
            "Un login correcto no deja secretos en los logs": f"{LEAKS}::test_successful_login_logs_no_secrets",
            "Un login fallido no deja secretos en los logs": f"{LEAKS}::test_failed_login_logs_no_secrets",
            "Las credenciales internas no muestran el hash": f"{MODEL}::test_credentials_repr_hides_hash",
            "La configuración no muestra los secretos": f"{CONFIG}::test_settings_repr_hides_secrets",
            "Un usuario duplicado no filtra el hash": f"{REPOSITORY}::test_duplicate_username_error_hides_hash",
            "Una regla de rol violada no filtra el hash": f"{REPOSITORY}::test_role_rule_error_hides_hash",
        },
        "Autorización documentada en Swagger": {
            "Esquema bearerAuth declarado": f"{OPENAPI}::test_bearer_scheme_is_declared",
            "La ruta del usuario autenticado tiene candado": f"{OPENAPI}::test_me_has_security_and_401",
            "El login no tiene candado": f"{OPENAPI}::test_login_has_no_security_and_documents_responses",
            "Salud no tiene candado": f"{OPENAPI}::test_health_has_no_security",
            "Una ruta con permiso documenta 403": f"{OPENAPI}::test_permission_route_documents_403",
            "Swagger conserva la autorización": f"{OPENAPI}::test_swagger_persists_authorization",
        },
    },
    "database-infrastructure": {
        "Tabla de usuarios con restricciones en la base": {
            "Usuario duplicado": f"{PERSISTENCE}::test_duplicate_username_is_rejected",
            "Usuario con mayúsculas": f"{PERSISTENCE}::test_uppercase_username_is_rejected",
            "Rol desconocido": f"{PERSISTENCE}::test_unknown_role_is_rejected",
            "Activo por defecto": f"{PERSISTENCE}::test_active_defaults_to_true",
            "Profesional inexistente": f"{PERSISTENCE}::test_unknown_professional_is_rejected",
            "Borrar un profesional con usuario": f"{PERSISTENCE}::test_deleting_professional_with_user_is_rejected",
        },
        "El odontólogo tiene profesional y los demás roles no": {
            "Odontólogo con profesional": f"{PERSISTENCE}::test_doctor_with_professional_is_accepted",
            "Odontólogo sin profesional": f"{PERSISTENCE}::test_doctor_without_professional_is_rejected",
            "Recepción sin profesional": f"{PERSISTENCE}::test_reception_without_professional_is_accepted",
            "Recepción con profesional": f"{PERSISTENCE}::test_reception_with_professional_is_rejected",
            "Administrador con profesional": f"{PERSISTENCE}::test_admin_with_professional_is_rejected",
            "Cambiar a recepción sin quitar el profesional": f"{PERSISTENCE}::test_changing_role_keeping_professional_is_rejected",
            "Dos usuarios para el mismo profesional": f"{PERSISTENCE}::test_two_users_for_same_professional_are_rejected",
            "Varios usuarios sin profesional": f"{PERSISTENCE}::test_several_users_without_professional_are_accepted",
        },
        "Migración reversible de usuarios": {
            "Downgrade a la revisión anterior": f"{INFRA}::test_user_migration_explicit_downgrade_cycle",
            "Upgrade a la revisión de usuarios": f"{INFRA}::test_user_migration_explicit_upgrade",
            "Sin diferencias con la metadata": f"{INFRA}::test_metadata_has_no_differences_with_users",
        },
        "Seed de un usuario por rol": {
            "Primera ejecución crea los tres usuarios": f"{SEED}::test_seed_creates_one_user_per_role",
            "Cada usuario del seed inicia sesión": f"{SEED}::test_seed_users_can_log_in",
            "Segunda ejecución no inserta": f"{SEED}::test_second_seed_inserts_nothing",
            "Una contraseña distinta no cambia a los usuarios existentes": f"{SEED}::test_seed_does_not_change_existing_password",
            "El seed guarda hash Argon2id": f"{SEED}::test_seed_stores_argon2id_hash",
            "El usuario y el profesional tienen ids distintos": f"{SEED}::test_seed_user_id_differs_from_professional_id",
            "La salida del seed no muestra la contraseña": f"{SEED}::test_seed_output_hides_password",
        },
        "El seed exige una contraseña válida antes de escribir": {
            "Falta la contraseña": f"{SEED}::test_seed_rejects_missing_password",
            "Contraseña vacía": f"{SEED}::test_seed_rejects_empty_password",
            "Contraseña de solo espacios": f"{SEED}::test_seed_rejects_blank_password",
            "Contraseña de 7 caracteres": f"{SEED}::test_seed_rejects_short_password",
            "Contraseña de 8 caracteres": f"{SEED}::test_seed_accepts_eight_characters",
            "El comando manual termina con error": f"{SEED}::test_seed_command_exits_with_error",
        },
        "El seed se niega a correr en producción": {
            "Seed con APP_ENV production": f"{SEED}::test_seed_refuses_production",
            "Seed con APP_ENV development": f"{SEED}::test_seed_runs_in_development",
        },
        "Configuración completa y errores explícitos": {
            "Falta DATABASE_URL": f"{CONFIG}::test_missing_database_url_names_variable",
            "Configuración completa": f"{CONFIG}::test_complete_configuration_exposes_typed_values",
            "Falta SEED_USER_PASSWORD": f"{CONFIG}::test_missing_seed_password_loads_as_none",
        },
        "Migración reversible de horarios y bloqueos": {
            "Ciclo upgrade y downgrade reversible de la migración": f"{INFRA}::test_availability_migration_downgrade_minus_one_cycle",
        },
        "Migración reversible de turnos e historial": {
            "Ciclo upgrade y downgrade menos uno de la migración de turnos": f"{INFRA}::test_appointment_migration_downgrade_minus_one_cycle",
        },
    },
}


def spec_scenarios(path: Path) -> list[tuple[str, str]]:
    scenarios: list[tuple[str, str]] = []
    requirement = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### Requirement: "):
            requirement = line.removeprefix("### Requirement: ").strip()
        elif line.startswith("#### Scenario: "):
            scenarios.append((requirement, line.removeprefix("#### Scenario: ").strip()))
    return scenarios


def collected_nodes() -> set[str]:
    environment = {**os.environ, "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [PYTHON, "-m", "pytest", "--collect-only", "-q", "-m", "integration or not integration"],
        cwd=BACKEND,
        env=environment,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {line.strip() for line in result.stdout.splitlines() if "::" in line}


def node_exists(node: str, nodes: set[str]) -> bool:
    return node in nodes or any(item.startswith(f"{node}[") for item in nodes)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    nodes = collected_nodes()
    problems: list[str] = []
    rows: list[str] = []
    number = 0
    for spec_name, path in (
        ("authentication-and-rbac", AUTH_SPEC),
        ("database-infrastructure", INFRA_SPEC),
    ):
        scenarios = spec_scenarios(path)
        mapped = {
            (requirement, scenario)
            for requirement, items in TRACE[spec_name].items()
            for scenario in items
        }
        for requirement, scenario in sorted(mapped - set(scenarios)):
            problems.append(f"sobra en el mapa: {spec_name} / {requirement} / {scenario}")
        for requirement, scenario in scenarios:
            number += 1
            node = TRACE[spec_name].get(requirement, {}).get(scenario)
            if node is None:
                problems.append(f"sin test: {spec_name} / {requirement} / {scenario}")
                continue
            if not node_exists(node, nodes):
                problems.append(f"test inexistente: {node}")
            rows.append(f"| {number} | {spec_name} | {requirement} | {scenario} | `{node}` |")

    table = "\n".join(
        [
            "| # | Spec | Requisito | Escenario | Test |",
            "|---|---|---|---|---|",
            *rows,
        ]
    )
    lines = [
        "Salida generada por docs/evidencias/trazabilidad-C-19.py. No editar a mano.",
        f"tests recolectados por pytest: {len(nodes)}",
        f"escenarios en las dos specs delta: {number}",
        f"escenarios con test recolectado: {len(rows) - sum(p.startswith('test inexistente') for p in problems)}",
        f"problemas: {len(problems)}",
        *problems,
    ]
    report = "\n".join(lines) + "\n"
    OUTPUT.write_text(report, encoding="utf-8", newline="\n")
    sys.stdout.write(report)

    verify = VERIFY.read_text(encoding="utf-8")
    start = verify.find(TABLE_START)
    end = verify.find(TABLE_END)
    if start == -1 or end == -1:
        print("Faltan los marcadores de trazabilidad en verify-C-19.md", file=sys.stderr)
        return 2
    VERIFY.write_text(
        f"{verify[: start + len(TABLE_START)]}\n{table}\n{verify[end:]}",
        encoding="utf-8",
        newline="\n",
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
