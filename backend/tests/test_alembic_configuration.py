from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_alembic_ini_uses_safe_configuration_without_database_url() -> None:
    alembic_ini = (BACKEND_ROOT / "alembic.ini").read_text(encoding="utf-8")

    assert "sqlalchemy.url" not in alembic_ini
    assert "script_location = %(here)s/alembic" in alembic_ini
    assert "file_template = %%Y%%m%%d_%%H%%M_%%slug" not in alembic_ini
    assert "file_template = %%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s" in alembic_ini
