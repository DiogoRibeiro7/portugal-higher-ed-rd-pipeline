"""Regression for the Study B 2020/2021 source-vintage revision audit."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "source_manifests" / "study_b_2020_2021_revision_audit.csv"
POLICY = ROOT / "config" / "study_b_source_vintage_revision_policy.yml"


def test_revision_audit_matches_frozen_policy_inventory() -> None:
    audit = pd.read_csv(AUDIT, dtype={"programme_code": str, "institution_code": str})
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))

    assert len(audit) == 2
    assert set(audit["overlap_year"]) == {2020}
    assert set(audit["programme_code"]) == {"9147"}
    assert set(audit["canonicalisation"]) == {"contemporary_source_vintage"}
    assert set(audit["difference"]) == {0.1}

    expected = {
        (
            str(item["programme_code"]),
            str(item["institution_code"]),
            str(item["measure"]),
            float(item["contemporary_2020_value"]),
            float(item["StatsCurso21_reported_2020_value"]),
        )
        for item in policy["observed_trigger_inventory"]["known_revisions"]
    }
    observed = {
        (
            str(row.programme_code),
            str(row.institution_code),
            str(row.measure),
            float(row.canonical_value),
            float(row.later_reported_value),
        )
        for row in audit.itertuples(index=False)
    }

    assert observed == expected
    assert set(audit["contemporary_source_vintage"]) == {2020}
    assert set(audit["later_source_vintage"]) == {2021}
