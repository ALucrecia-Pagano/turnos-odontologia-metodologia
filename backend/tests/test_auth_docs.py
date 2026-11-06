from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE = REPO_ROOT / "knowledge-base"


def read_kb(name: str) -> str:
    return (KNOWLEDGE_BASE / name).read_text(encoding="utf-8")


def test_kb_04_documents_app_user() -> None:
    content = read_kb("04_modelo_de_datos.md")

    assert "app_user" in content
    assert "ck_app_user_professional_by_role" in content
    assert "`changed_by`" in content
    assert "relación lógica" in content


def test_kb_09_registers_author_decisions() -> None:
    content = read_kb("09_decisiones_y_supuestos.md")

    # D5: el usuario se confirma contra la base en cada request.
    assert "en cada request" in content
    # D17: sin ABM de usuarios en el MVP.
    assert "ABM de usuarios" in content
    # P4: el active del usuario y el del profesional son independientes.
    assert "INACTIVE_REFERENCE" in content
    assert "profesional desactivado" in content


def test_kb_10_keeps_su_06_pending() -> None:
    content = read_kb("10_preguntas_abiertas.md")

    pending = [line for line in content.splitlines() if "SU-06" in line and "cátedra" in line]
    assert any("pendiente de confirmar" in line for line in pending)


def test_kb_03_documents_doctor_reading_scope() -> None:
    content = read_kb("03_actores_y_roles.md")

    agenda_row = next(
        line for line in content.splitlines() if line.startswith("| Turnos (leer agenda)")
    )
    assert "R (todos, solo lectura" in agenda_row.split("|")[2]
    assert "ABM de usuarios" in content


def test_readme_documents_seed_and_secret() -> None:
    content = (REPO_ROOT / "backend" / "README.md").read_text(encoding="utf-8")

    for username in ("administrador", "recepcion", "odontologo"):
        assert f"`{username}`" in content
    assert "SEED_USER_PASSWORD" in content
    assert "no cambia a los usuarios existentes" in content
    assert "secrets.token_urlsafe(48)" in content
    assert "al menos 32 caracteres" in content


def test_kb_08_documents_optional_seed_password() -> None:
    content = read_kb("08_arquitectura_propuesta.md")

    row = next(line for line in content.splitlines() if line.startswith("| `SEED_USER_PASSWORD`"))
    assert "Opcional para la API" in row
    assert "la exige el seed" in row
