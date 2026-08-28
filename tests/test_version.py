"""Release-version consistency checks."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pt_he_pipeline import __version__


def test_package_version_matches_pyproject() -> None:
    """Keep the runtime package version aligned with the project metadata."""
    root = Path(__file__).resolve().parents[1]
    with (root / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)

    assert isinstance(project, dict)
    poetry = project.get("tool", {}).get("poetry", {})
    assert isinstance(poetry, dict)
    project_version = poetry.get("version")
    assert isinstance(project_version, str)
    assert __version__ == project_version
