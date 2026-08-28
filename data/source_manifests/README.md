# Source manifests

`dges_first_phase.csv` is a **registered acquisition plan**, not a receipt file and
not evidence that the corresponding provider bytes have already been downloaded.

The manifest separates:

- 1997-2003: official annual archive discovery without pre-assuming a detailed
  pair-index URL;
- 2004-2025: the verified standard `statcol`/`statce` URL family;
- 2026: the current first-phase placements route, treated as a partial vintage.

Rebuild it with:

```bash
poetry run pt-he-pipeline dges-manifest \
  --output data/source_manifests/dges_first_phase.parquet
```

`dges_study_a_recent.csv` has a different role. It registers the exact official
first-phase result note and Quadro V table used for the v0.3 2023-2026 curated
baseline. It is a source index for a publication-table transcription, not a
provider-file download receipt.

Actual raw acquisitions live under `data/raw/` and receive adjacent JSON SHA-256
receipts.
