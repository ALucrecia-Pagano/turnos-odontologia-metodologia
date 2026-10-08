import importlib
from pathlib import Path


def test_domain_package_is_importable_package() -> None:
    domain = importlib.import_module("app.domain")

    assert domain.__spec__ is not None
    assert domain.__spec__.submodule_search_locations
    assert list(domain.__path__)


def test_domain_package_resolves_to_repo_directory() -> None:
    domain = importlib.import_module("app.domain")
    expected = Path(__file__).parents[2] / "app" / "domain"

    assert domain.__file__ is not None
    assert Path(domain.__file__).parent.resolve() == expected.resolve()
