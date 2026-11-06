from app.auth.model import AuthenticatedUser
from app.auth.passwords import candidate_password_hash, verify_password
from app.repositories.users import UserRepository


def authenticate(
    repository: UserRepository, username: str, password: str
) -> AuthenticatedUser | None:
    """Devuelve el usuario, o `None` si las credenciales no son válidas.

    Los tres casos inválidos ejecutan los mismos pasos: un usuario inexistente se
    verifica contra el hash ficticio, y `active` se mira al final.
    """
    credentials = repository.get_credentials_by_username(username.strip().lower())
    password_ok = verify_password(candidate_password_hash(credentials), password)
    if credentials is None or not password_ok or not credentials.active:
        return None
    return credentials.user
