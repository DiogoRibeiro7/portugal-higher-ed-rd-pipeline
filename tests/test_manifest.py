from __future__ import annotations

import pandas as pd

from pt_he_pipeline.manifest import build_dges_vintage_manifest


def test_manifest_registers_three_acquisition_eras() -> None:
    frame = build_dges_vintage_manifest(2003, 2026)
    row_2003 = frame.loc[frame["year"] == 2003].iloc[0]
    row_2004 = frame.loc[frame["year"] == 2004].iloc[0]
    row_2026 = frame.loc[frame["year"] == 2026].iloc[0]
    assert pd.isna(row_2003["pair_index_url"])
    assert "col04f1" in row_2004["pair_index_url"]
    assert row_2026["acquisition_mode"] == "current_results_adapter"
    assert row_2026["status"] == "partial_current_vintage"
