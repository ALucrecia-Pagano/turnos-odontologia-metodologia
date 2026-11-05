from sqlalchemy.exc import IntegrityError


def constraint_name(error: IntegrityError) -> str | None:
    original = error.orig
    diagnostic = getattr(original, "diag", None)
    name = getattr(diagnostic, "constraint_name", None)
    return name if isinstance(name, str) else None

