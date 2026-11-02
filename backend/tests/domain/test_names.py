import pytest

from app.domain.rules.names import subject_name


@pytest.mark.parametrize(
    ("name", "generic", "expected"),
    [
        pytest.param("Dra. Laura Quiroga", "El profesional", "Dra. Laura Quiroga", id="con-nombre"),
        pytest.param("Sillón 1", "El sillón", "Sillón 1", id="sillon-con-nombre"),
        pytest.param("", "El profesional", "El profesional", id="vacio"),
        pytest.param("", "el profesional", "el profesional", id="vacio-en-minuscula"),
        pytest.param("   ", "El profesional", "El profesional", id="en-blanco"),
        pytest.param("\t \n", "El profesional", "El profesional", id="en-blanco-con-tabs"),
        pytest.param(
            "  Dra. Laura Quiroga  ", "El profesional", "Dra. Laura Quiroga", id="recortado"
        ),
        pytest.param(" Sillón 1\t", "El sillón", "Sillón 1", id="recortado-con-tab"),
    ],
)
def test_subject_name_returns_trimmed_name_or_generic_noun(
    name: str, generic: str, expected: str
) -> None:
    assert subject_name(name, generic) == expected
