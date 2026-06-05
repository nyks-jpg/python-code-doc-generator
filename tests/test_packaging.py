from pathlib import Path

from main import APP_VERSION

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib


def test_pyproject_metadata_is_release_ready() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]

    assert project["name"] == "python-code-doc-generator"
    assert project["version"] == APP_VERSION
    assert project["requires-python"] == ">=3.10"
    assert project["license"] == "MIT"
    assert project["license-files"] == ["LICENSE"]
    assert "python-code-doc-generator" in project["scripts"]


def test_pyproject_includes_runtime_modules() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    modules = metadata["tool"]["setuptools"]["py-modules"]

    assert "main" in modules
    assert "doc_providers" in modules
