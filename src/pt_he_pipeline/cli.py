"""Command-line interface for DGES acquisition, parsing and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import typer

from pt_he_pipeline.acquisition import acquire_standard_dges_vintage
from pt_he_pipeline.dges import discover_documents
from pt_he_pipeline.dges_pair import parse_pair_statistics_pdf
from pt_he_pipeline.dges_placements import parse_placement_excel, parse_placement_pdf
from pt_he_pipeline.ingestion import build_cna_pairs
from pt_he_pipeline.io import fetch_with_receipt
from pt_he_pipeline.manifest import build_dges_vintage_manifest
from pt_he_pipeline.mobility import parse_mobility_pdf, select_preferred_mobility_vintage
from pt_he_pipeline.reporting import pair_coverage_report
from pt_he_pipeline.validation import validate_mobility_flows, validate_pair_panel

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _read_table(path: Path) -> pd.DataFrame:
    """Read a supported canonical table from disk."""

    if not path.is_file():
        raise typer.BadParameter(f"file not found: {path}")
    suffixes = [suffix.casefold() for suffix in path.suffixes]
    if path.suffix.casefold() == ".parquet":
        return pd.read_parquet(path)
    if ".csv" in suffixes:
        return pd.read_csv(path)
    raise typer.BadParameter("supported formats are .parquet and .csv/.csv.gz")


def _write_table(frame: pd.DataFrame, path: Path) -> None:
    """Write a canonical table deterministically by extension."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.casefold() == ".parquet":
        frame.to_parquet(path, index=False)
    elif path.suffix.casefold() == ".csv":
        frame.to_csv(path, index=False, lineterminator="\n")
    else:
        raise typer.BadParameter("output must end in .parquet or .csv")


@app.command("discover-dges")
def discover_dges(year: int = typer.Option(..., min=1997, max=2100)) -> None:
    """Discover official document links on a DGES annual statistics page."""

    documents = discover_documents(year)
    typer.echo(json.dumps(documents, indent=2, sort_keys=True, ensure_ascii=False))


@app.command("dges-manifest")
def dges_manifest(
    output: Path | None = typer.Option(None),
    start_year: int = typer.Option(1997, min=1997),
    end_year: int = typer.Option(2026, min=1997),
) -> None:
    """Build the registered DGES acquisition-vintage manifest."""

    frame = build_dges_vintage_manifest(start_year, end_year)
    if output is None:
        typer.echo(frame.to_csv(index=False, lineterminator="\n"))
        return
    _write_table(frame, output)
    typer.echo(f"Wrote {len(frame):,} vintages to {output}")


@app.command("acquire-dges-year")
def acquire_dges_year_command(
    year: int = typer.Option(..., min=1997, max=2025),
    raw_root: Path = typer.Option(Path("data/raw")),
    overwrite: bool = typer.Option(False),
) -> None:
    """Acquire the standard DGES source bundle with content receipts."""

    log = acquire_standard_dges_vintage(year, raw_root=raw_root, overwrite=overwrite)
    typer.echo(log.to_csv(index=False, lineterminator="\n"))


@app.command("fetch")
def fetch(
    url: str = typer.Option(...),
    output: Path = typer.Option(...),
    overwrite: bool = typer.Option(False),
) -> None:
    """Download a source and write its SHA-256 provenance receipt."""

    receipt = fetch_with_receipt(url, output, overwrite=overwrite)
    typer.echo(
        json.dumps(
            {
                "path": str(receipt.path),
                "sha256": receipt.sha256,
                "size_bytes": receipt.size_bytes,
                "retrieved_at_utc": receipt.retrieved_at_utc,
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("parse-pair-pdf")
def parse_pair_pdf_command(
    source: Path = typer.Option(...),
    year: int = typer.Option(..., min=1997, max=2100),
    phase: int = typer.Option(1, min=1, max=3),
    output: Path = typer.Option(...),
) -> None:
    """Parse a DGES all-pairs/detail PDF into a canonical interim table."""

    frame = parse_pair_statistics_pdf(source, year=year, phase=phase)
    _write_table(frame, output)
    typer.echo(f"Wrote {len(frame):,} pair-statistics rows to {output}")


@app.command("parse-placement")
def parse_placement_command(
    source: Path = typer.Option(...),
    year: int = typer.Option(..., min=1997, max=2100),
    phase: int = typer.Option(1, min=1, max=3),
    output: Path = typer.Option(...),
) -> None:
    """Parse a DGES vacancy/placement PDF or Excel file."""

    suffix = source.suffix.casefold()
    if suffix == ".pdf":
        frame = parse_placement_pdf(source, year=year, phase=phase)
    elif suffix in {".xls", ".xlsx"}:
        frame = parse_placement_excel(source, year=year, phase=phase)
    else:
        raise typer.BadParameter("source must be .pdf, .xls or .xlsx")
    _write_table(frame, output)
    typer.echo(f"Wrote {len(frame):,} placement rows to {output}")


@app.command("parse-mobility")
def parse_mobility_command(
    source: Path = typer.Option(...),
    source_document_year: int = typer.Option(..., min=1997, max=2100),
    output: Path = typer.Option(...),
) -> None:
    """Parse all current/previous-year matrices from a DGES mobility PDF."""

    frame = parse_mobility_pdf(source, source_document_year=source_document_year)
    _write_table(frame, output)
    typer.echo(f"Wrote {len(frame):,} mobility cells to {output}")


@app.command("select-mobility-vintages")
def select_mobility_vintages_command(
    source: Path = typer.Option(...),
    output: Path = typer.Option(...),
) -> None:
    """Choose the preferred copy of duplicated comparative mobility matrices."""

    result = select_preferred_mobility_vintage(_read_table(source))
    validate_mobility_flows(result)
    _write_table(result, output)
    typer.echo(f"Wrote {len(result):,} preferred mobility cells to {output}")


@app.command("validate-mobility")
def validate_mobility_command(source: Path = typer.Option(...)) -> None:
    """Validate a canonical long-form mobility table."""

    frame = _read_table(source)
    validate_mobility_flows(frame)
    typer.echo(f"OK: {len(frame):,} mobility cells")


@app.command("build-cna-pairs")
def build_cna_pairs_command(
    pair_statistics: Path = typer.Option(...),
    placements: Path = typer.Option(...),
    output: Path = typer.Option(...),
) -> None:
    """Join pair statistics to vacancy/placement data with consistency checks."""

    result = build_cna_pairs(_read_table(pair_statistics), _read_table(placements))
    _write_table(result, output)
    typer.echo(f"Wrote {len(result):,} canonical CNA rows to {output}")


@app.command("coverage-report")
def coverage_report_command(
    source: Path = typer.Option(...),
    output: Path | None = typer.Option(None),
) -> None:
    """Report row counts and key-field missingness by year and phase."""

    report = pair_coverage_report(_read_table(source))
    if output is None:
        typer.echo(report.to_csv(index=False, lineterminator="\n"))
        return
    _write_table(report, output)
    typer.echo(f"Wrote coverage report to {output}")


@app.command("validate-pair-panel")
def validate_pair_panel_command(path: Path) -> None:
    """Validate a canonical CNA pair table in Parquet or CSV format."""

    frame = _read_table(path)
    validate_pair_panel(frame)
    typer.echo(f"OK: {len(frame):,} rows")


if __name__ == "__main__":
    app()
