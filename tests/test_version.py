"""Release-version consistency checks."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import yaml

from pt_he_pipeline import __version__

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping and reject malformed top-level structures."""
    with path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    assert isinstance(payload, dict)
    return payload


def _project_version() -> str:
    """Return the canonical version from ``pyproject.toml``."""
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)

    assert isinstance(project, dict)
    poetry = project.get("tool", {}).get("poetry", {})
    assert isinstance(poetry, dict)
    version = poetry.get("version")
    assert isinstance(version, str)
    return version


def test_release_versions_are_consistent() -> None:
    """Keep runtime, project, citation and study metadata on one release version."""
    expected = _project_version()

    citation = _load_yaml(ROOT / "CITATION.cff")
    citation_version = citation.get("version")
    assert isinstance(citation_version, str)

    study = _load_yaml(ROOT / "config" / "study.yml")
    project = study.get("project")
    assert isinstance(project, dict)
    study_version = project.get("version")
    assert isinstance(study_version, str)

    assert __version__ == expected
    assert citation_version == expected
    assert study_version == expected
