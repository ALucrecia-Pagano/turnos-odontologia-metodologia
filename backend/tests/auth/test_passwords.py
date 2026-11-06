from pathlib import Path
from uuid import UUID

from app.auth.model import AuthenticatedUser, UserCredentials
from app.auth.passwords import hash_password, verify_password
from app.domain.model import Role
from tests.auth.hashes import cheap_hash


PRODUCTION_PREFIX = "$argon2id$v=19$m=65536,t=3,p=4$"
APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def test_hash_uses_fixed_parameters() -> None:
    assert hash_password("clave-ficticia").startswith(PRODUCTION_PREFIX)


def test_same_password_hashes_differ() -> None:
    assert hash_password("clave-ficticia") != hash_password("clave-ficticia")


def test_correct_password_verifies() -> None:
    assert verify_password(hash_password("clave-ficticia"), "clave-ficticia") is True


def test_wrong_password_does_not_verify() -> None:
    assert verify_password(hash_password("clave-ficticia"), "otra-clave") is False


def test_verify_uses_parameters_in_hash() -> None:
    stored = cheap_hash("clave-ficticia")

    assert not stored.startswith(PRODUCTION_PREFIX)
    assert verify_password(stored, "clave-ficticia") is True
    assert verify_password(stored, "otra-clave") is False


def test_corrupt_hash_does_not_verify() -> None:
    assert verify_password("esto-no-es-un-hash", "clave-ficticia") is False
    assert verify_password("", "clave-ficticia") is False


def test_cheapest_profile_not_in_production() -> None:
    offenders = [
        path
        for path in APP_ROOT.rglob("*.py")
        if "CHEAPEST" in path.read_text(encoding="utf-8")
    ]

    assert list(APP_ROOT.rglob("*.py")) != []
    assert offenders == []


def test_missing_user_uses_dummy_hash() -> None:
    from app.auth.passwords import candidate_password_hash, dummy_password_hash

    chosen = candidate_password_hash(None)

    assert chosen == dummy_password_hash()
    assert chosen.startswith(PRODUCTION_PREFIX)


def test_existing_credentials_use_stored_hash() -> None:
    from app.auth.passwords import candidate_password_hash

    credentials = UserCredentials(
        user=AuthenticatedUser(
            id=UUID(int=1),
            username="recepcion",
            display_name="Recepción de Prueba",
            role=Role.RECEPCION,
            professional_id=None,
        ),
        active=True,
        password_hash="hash-guardado",
    )

    assert candidate_password_hash(credentials) == "hash-guardado"
