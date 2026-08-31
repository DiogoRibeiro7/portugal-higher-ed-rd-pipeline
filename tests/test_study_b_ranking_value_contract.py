"""Release-contract tests for the non-redistributed Study B ranking panel."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "data" / "source_manifests" / "study_b_ranking_value_contract.json"
MANIFEST = ROOT / "data" / "source_manifests" / "study_b_ranking_value_sources.csv"
COVERAGE = ROOT / "results" / "study_b" / "ranking_coverage.csv"


def test_contract_matches_frozen_provider_membership_counts() -> None:
    """Private-panel counts must equal the verified parent counts in release coverage."""
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    coverage = pd.read_csv(COVERAGE)
    expected = contract["expected_provider_year_counts"]

    for provider, years in expected.items():
        for year, count in years.items():
            row = coverage.loc[
                (coverage["provider"] == provider)
                & (coverage["admission_year"] == int(year))
            ].iloc[0]
            assert int(row["verified_ranked_parent_institutions"]) == int(count)

    assert sum(
        int(count)
        for years in expected.values()
        for count in years.values()
    ) == int(contract["expected_rows"])


def test_manifest_uses_one_eligible_edition_per_provider_year() -> None:
    """Every frozen provider/year cell must have exactly one dated source contract."""
    manifest = pd.read_csv(MANIFEST)
    assert len(manifest) == 9
    assert not manifest.duplicated(["provider", "admission_year"]).any()
    publication = pd.to_datetime(manifest["publication_date"], errors="raise")
    deadline = pd.to_datetime(manifest["application_deadline"], errors="raise")
    assert (publication <= deadline).all()
    assert not manifest["redistribute_values"].astype(bool).any()


def test_private_panel_contract_preserves_registered_representation_rules() -> None:
    """The value gate must preserve bands, missingness and non-redistribution rules."""
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    rules = contract["rules"]
    assert rules["exact_rank_and_band_mutually_exclusive"] is True
    assert rules["rank_band_midpoints_forbidden"] is True
    assert rules["candidate_only_entries_excluded"] is True
    assert rules["publication_after_application_deadline_forbidden"] is True
    assert rules["provider_values_must_not_be_committed"] is True
    assert contract["private_panel_tracked"] is False
    assert len(str(contract["canonical_sha256"])) == 64
