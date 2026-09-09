"""Run an auditable local validation of an exact release-candidate checkout."""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import time
import tomllib
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_ROOT = ROOT / "validation" / "results"
VALIDATION_PREFIX = "validation/results/"
PAPER_DIR = ROOT / "paper"


@dataclass(frozen=True)
class Step:
    """One release-validation command and its execution directory."""

    name: str
    command: tuple[str, ...]
    cwd: Path


@dataclass(frozen=True)
class StepResult:
    """Recorded outcome for one validation step."""

    name: str
    command: tuple[str, ...]
    returncode: int
    duration_seconds: float
    log_path: str

    @property
    def passed(self) -> bool:
        """Return whether the command completed successfully."""
        return self.returncode == 0


def _run_text(command: Sequence[str], cwd: Path = ROOT) -> str:
    """Run a small command and return stripped standard output."""
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _git(*args: str) -> str:
    """Run a Git command from the repository root."""
    return _run_text(("git", *args))


def _release_version() -> str:
    """Read the canonical package version from ``pyproject.toml``."""
    with (ROOT / "pyproject.toml").open("rb") as handle:
        payload = tomllib.load(handle)

    tool = payload.get("tool")
    if not isinstance(tool, dict):
        raise ValueError("pyproject.toml does not contain a [tool] mapping")
    poetry = tool.get("poetry")
    if not isinstance(poetry, dict):
        raise ValueError("pyproject.toml does not contain a [tool.poetry] mapping")
    version = poetry.get("version")
    if not isinstance(version, str):
        raise ValueError("pyproject.toml does not contain a string Poetry version")
    return version


def _outside_validation_results(status_lines: Sequence[str]) -> list[str]:
    """Return Git status entries that are not validator-generated evidence."""
    outside: list[str] = []
    for line in status_lines:
        path = line[3:] if len(line) >= 4 else line
        if " -> " in path:
            path = path.split(" -> ", maxsplit=1)[1]
        if path == "validation/results" or path.startswith(VALIDATION_PREFIX):
            continue
        outside.append(line)
    return outside


def _working_tree_changes() -> list[str]:
    """Return non-validation changes in the current checkout."""
    status = _git("status", "--porcelain=v1", "--untracked-files=all")
    return _outside_validation_results(status.splitlines())


def _steps() -> tuple[Step, ...]:
    """Return the complete local validation sequence."""
    python = ("poetry", "run", "python")
    return (
        Step("poetry-check", ("poetry", "check", "--lock"), ROOT),
        Step("poetry-install", ("poetry", "install", "--no-interaction"), ROOT),
        Step("ruff", ("poetry", "run", "ruff", "check", "."), ROOT),
        Step("mypy", ("poetry", "run", "mypy", "src"), ROOT),
        Step(
            "pytest",
            (
                "poetry",
                "run",
                "pytest",
                "--cov=pt_he_pipeline",
                "--cov-report=term-missing",
            ),
            ROOT,
        ),
        Step("study-a-recent", (*python, "scripts/build_study_a_recent.py"), ROOT),
        Step("study-a-medium-run", (*python, "scripts/build_study_a_medium_run.py"), ROOT),
        Step("study-a-age18", (*python, "scripts/build_study_a_age18.py"), ROOT),
        Step("study-a-demographic", (*python, "scripts/build_study_a_demographic.py"), ROOT),
        Step("study-b-pilot", (*python, "scripts/build_study_b_course9119_pilot.py"), ROOT),
        Step("study-b-multi-course", (*python, "scripts/build_study_b_multi_course.py"), ROOT),
        Step("study-b-regionality", (*python, "scripts/build_study_b_regionality.py"), ROOT),
        Step(
            "study-b-ranking-coverage",
            (*python, "scripts/build_study_b_ranking_coverage.py"),
            ROOT,
        ),
        Step(
            "paper-pass-1",
            ("pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"),
            PAPER_DIR,
        ),
        Step(
            "paper-pass-2",
            ("pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"),
            PAPER_DIR,
        ),
    )


def _run_step(step: Step, output_dir: Path, index: int) -> StepResult:
    """Execute one validation step and persist its combined command output."""
    log_path = output_dir / f"{index:02d}-{step.name}.log"
    started = time.monotonic()
    try:
        completed = subprocess.run(
            step.command,
            cwd=step.cwd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        output = completed.stdout
        returncode = completed.returncode
    except OSError as exc:
        output = f"Unable to execute command: {exc}\n"
        returncode = 127

    duration = time.monotonic() - started
    log_path.write_text(output, encoding="utf-8")
    print(output, end="" if output.endswith("\n") else "\n")
    return StepResult(
        name=step.name,
        command=step.command,
        returncode=returncode,
        duration_seconds=round(duration, 3),
        log_path=str(log_path.relative_to(ROOT)),
    )


def _tool_version(command: Sequence[str]) -> str | None:
    """Return the first output line for an optional external tool."""
    try:
        output = _run_text(command)
    except (OSError, subprocess.CalledProcessError):
        return None
    return output.splitlines()[0] if output else None


def _render_summary(
    *,
    commit: str,
    version: str,
    results: Sequence[StepResult],
    dirty_after: Sequence[str],
    passed: bool,
) -> str:
    """Render the human-readable local validation summary."""
    status = "LOCAL PASS" if passed else "LOCAL FAIL"
    lines = [
        f"# Release validation — {status}",
        "",
        f"- Commit: `{commit}`",
        f"- Version: `{version}`",
        f"- Result: **{status}**",
        "",
        "A local pass is evidence for this exact checkout only. It does not make the commit",
        "tag-ready: the hosted GitHub Actions gate must still execute successfully before the",
        "v0.3.4 tag or GitHub release is created.",
        "",
        "## Steps",
        "",
        "| Step | Result | Seconds | Log |",
        "|---|---|---:|---|",
    ]
    for result in results:
        outcome = "pass" if result.passed else f"fail ({result.returncode})"
        lines.append(
            f"| `{result.name}` | {outcome} | {result.duration_seconds:.3f} | "
            f"`{result.log_path}` |"
        )

    if dirty_after:
        lines.extend(["", "## Unexpected working-tree changes", ""])
        lines.extend(f"- `{entry}`" for entry in dirty_after)

    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: object) -> None:
    """Write deterministic, readable JSON evidence."""
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    """Validate the exact checkout and write auditable local evidence."""
    commit = _git("rev-parse", "HEAD")
    version = _release_version()
    output_dir = RESULTS_ROOT / commit

    initial_changes = _working_tree_changes()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "commit": commit,
        "platform": platform.platform(),
        "poetry": _tool_version(("poetry", "--version")),
        "python": sys.version,
        "started_at_utc": datetime.now(UTC).isoformat(),
        "version": version,
    }
    _write_json(output_dir / "metadata.json", metadata)

    if initial_changes:
        summary = _render_summary(
            commit=commit,
            version=version,
            results=(),
            dirty_after=initial_changes,
            passed=False,
        )
        (output_dir / "RELEASE_VALIDATION_LOCAL.md").write_text(summary, encoding="utf-8")
        print("Release validation refused: checkout is not clean.")
        return 2

    results: list[StepResult] = []
    for index, step in enumerate(_steps(), start=1):
        print(f"\n==> {step.name}: {' '.join(step.command)}")
        result = _run_step(step, output_dir, index)
        results.append(result)
        if not result.passed:
            break

    dirty_after = _working_tree_changes()
    passed = bool(results) and all(result.passed for result in results) and not dirty_after
    summary = _render_summary(
        commit=commit,
        version=version,
        results=results,
        dirty_after=dirty_after,
        passed=passed,
    )
    (output_dir / "RELEASE_VALIDATION_LOCAL.md").write_text(summary, encoding="utf-8")
    _write_json(
        output_dir / "validation.json",
        {
            "commit": commit,
            "dirty_after": list(dirty_after),
            "passed": passed,
            "results": [asdict(result) | {"passed": result.passed} for result in results],
            "version": version,
        },
    )

    print(f"\n{summary.splitlines()[0]}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
