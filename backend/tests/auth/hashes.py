"""Hash barato solo para datos de prueba: `verify` usa los parámetros del hash.

En producción no existe ningún camino que baje el costo: esto vive solo en tests.
"""

from argon2 import PasswordHasher
from argon2.profiles import CHEAPEST

_CHEAP_HASHER = PasswordHasher.from_parameters(CHEAPEST)


def cheap_hash(password: str) -> str:
    return _CHEAP_HASHER.hash(password)
