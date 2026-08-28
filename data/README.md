# Data directory

The repository does not commit provider datasets by default.

- `source_manifests/` — registered acquisition plans and public-source indexes;
  these are not raw download receipts.
- `raw/` — immutable provider source files and adjacent JSON receipts.
- `curated/` — small, explicitly documented transcriptions or hand-checked public
  aggregate tables when raw provider bytes are not bundled. These are never
  labelled as raw data and must reconcile to published control totals.
- `interim/` — parser outputs and concordance work.
- `processed/` — canonical analysis tables.

The Study A publication-table layers use curated DGES broad-area tables whose
source manifests identify the official documents. The demographic sensitivity also
commits the published INE/PORDATA 15-24 population values used to construct its
average single-year cohort proxy. These curated inputs remain distinct from raw
provider files and never receive invented provider-file digests. The v0.3.3 matched-course
source table follows the same rule: it contains 92 curated rows from two official DGES
comparative-course publications, including the duplicated 2019 records used for exact
cross-vintage reconciliation before the 69-row analytical panel is produced.

Use the separate raw digest columns and combined lineage fingerprints defined in
`docs/data_contracts.md`. Never infer that a source was acquired merely because
its URL appears in a manifest.
