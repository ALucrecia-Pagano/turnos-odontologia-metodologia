from functools import cache
from secrets import token_urlsafe

from argon2 import PasswordHasher, Type
from argon2.exceptions import Argon2Error, InvalidHashError

from app.auth.model import UserCredentials

# Parámetros literales (RFC 9106, perfil de baja memoria): una actualización de la
# librería no los cambia, y ninguna configuración los baja.
_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


def hash_password(password: str) -> str:
    return _HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _HASHER.verify(password_hash, password)
    except (Argon2Error, InvalidHashError):
        return False


@cache
def dummy_password_hash() -> str:
    """Hash de un valor aleatorio, con el costo de producción, una vez por proceso."""
    return hash_password(token_urlsafe(32))


def candidate_password_hash(credentials: UserCredentials | None) -> str:
    if credentials is None:
        return dummy_password_hash()
    return credentials.password_hash
