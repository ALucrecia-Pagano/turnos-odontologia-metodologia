from uuid import UUID

from app.auth.model import AuthenticatedUser, UserCredentials
from app.domain.model import Role


def test_credentials_repr_hides_hash() -> None:
    credentials = UserCredentials(
        user=AuthenticatedUser(
            id=UUID(int=1),
            username="recepcion",
            display_name="Recepción de Prueba",
            role=Role.RECEPCION,
            professional_id=None,
        ),
        active=True,
        password_hash="hash-ficticio-reconocible",
    )

    assert "hash-ficticio-reconocible" not in repr(credentials)
    assert "hash-ficticio-reconocible" not in str(credentials)
    assert credentials.password_hash == "hash-ficticio-reconocible"
