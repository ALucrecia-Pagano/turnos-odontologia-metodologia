import importlib.metadata
from pathlib import Path
import tomllib


def test_api_dependencies_are_declared() -> None:
    pyproject_path = Path(__file__).parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    dependencies = data["project"]["dependencies"]
    dev_dependencies = data["project"]["optional-dependencies"]["dev"]

    assert "fastapi>=0.118,<1" in dependencies
    assert "uvicorn>=0.30,<1" in dependencies
    assert "python-dotenv>=1,<2" in dependencies
    assert "httpx>=0.27,<1" in dev_dependencies


def test_api_dependencies_are_installed() -> None:
    for pkg in ("fastapi", "uvicorn", "httpx", "python-dotenv"):
        assert importlib.metadata.version(pkg) is not None

