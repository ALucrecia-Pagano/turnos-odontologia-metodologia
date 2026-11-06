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



def test_auth_dependencies_are_declared() -> None:
    pyproject_path = Path(__file__).parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

    dependencies = data["project"]["dependencies"]

    assert "PyJWT>=2.10,<3" in dependencies
    assert "argon2-cffi>=23.1,<26" in dependencies


def test_auth_dependencies_are_installed() -> None:
    pyjwt_major, pyjwt_minor = importlib.metadata.version("PyJWT").split(".")[:2]
    argon2_major = importlib.metadata.version("argon2-cffi").split(".")[0]

    assert int(pyjwt_major) == 2
    assert int(pyjwt_minor) >= 10
    assert 23 <= int(argon2_major) < 26
