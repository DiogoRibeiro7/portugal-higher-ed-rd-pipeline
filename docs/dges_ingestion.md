# DGES historical ingestion

## Purpose

Version 0.2 introduces the deterministic ingestion layer for Studies A and B. The target is not to scrape whatever happens to be visible on a web page. It is to preserve an auditable chain from official DGES bytes to canonical institution–programme–year rows and mobility flows.

The pipeline keeps **source discovery**, **raw acquisition**, **semantic parsing**, **cross-source reconciliation**, **concordance**, and **analysis metrics** as separate stages.

## Registered source vintages

DGES currently exposes the national-access statistical archive for 1997–2025. The repository therefore registers 1997 as the earliest target year rather than silently extrapolating earlier URL conventions.

Three acquisition eras are distinguished:

| Years | Mode | Rule |
|---|---|---|
| 1997–2003 | annual archive discovery | use the official annual statistics index; do not pre-assume a detailed `statce` URL |
| 2004–2025 | standard `statcol` + `statce` | discover annual documents and use the verified detailed pair-index URL family |
| 2026 | current-results adapter | use the first-phase placements release; do not pretend that the final annual statistics bundle already exists |

The machine-readable plan is `data/source_manifests/dges_first_phase.csv` and is reproducible with `pt-he-pipeline dges-manifest`.

## Source families

### Pair statistics

The detailed institution–programme sheets contain the variables needed to distinguish demand from realised placement:

- total applicants;
- first-choice applicants;
- placed students;
- mean application grade of placed students;
- general-contingent cut-off when a general-contingent placement exists.

The semantic sheet structure is stable in verified examples from 2004 and 2024/2025. Parsing therefore uses section names such as `OPÇÃO CANDIDATURA`, `ETAPA COLOCAÇÃO` and `MÉDIAS DOS COLOCADOS`, not hard-coded page coordinates.

A page that contains an institution/course code but fails semantic parsing is a hard error. Cover pages and non-data pages may be skipped.

### Vacancies, placements and cut-offs

A second source family provides initial vacancies, placements, cut-offs and remaining places. Column layouts have changed over time, so the parser uses stable identifiers and the numeric tail rather than a single fixed PDF coordinate map.

For current 2026 data, DGES publishes both Excel and PDF first-phase placement results. The Excel adapter is preferred where available because the 2026 PDF text layer can concatenate adjacent rows. Header matching is semantic and supports historical Portuguese label variants.

The placement count occurs in both the pair-statistics source and the vacancy/cut-off source. The canonical join treats a disagreement as a **release-blocking error** rather than choosing one silently.

### Mobility

Recent annual mobility PDFs are comparative: one source document can contain both the current competition year and the previous one, each with first-choice and placement matrices. Every parsed cell therefore records both:

- `year`: the competition year represented by the matrix;
- `source_document_year`: the annual document from which the matrix was extracted.

When two annual files contain the same matrix, the canonical selector prefers the matrix carried by its own competition year's document and uses a later comparative copy only as a backfill.

The origin dimension also has a historical comparability issue. Modern tables are described as district/GAES of application, while older files may contain access areas such as `Tâmega`. The schema therefore uses:

- `origin_area`;
- `origin_area_type = district | autonomous_region | access_area`;
- `destination_district`.

An access area is **not** relabelled as a district. Same-district statistics must report the share of flows covered by a comparable district/autonomous-region origin definition.

## Canonical pair construction

The principal join key is

```text
year × phase × source institution code × source course code
```

The canonical `cna_pairs` table retains raw source codes alongside harmonised identifiers. In v0.2, harmonised identifiers default to the source identifiers until an explicit concordance is approved.

Automatic fuzzy programme merging is deliberately forbidden. Programme names, institutions and degree structures can change for substantive reasons, including restructurings around the Bologna process. The concordance layer generates exact-code and exact-normalised-label candidates; ambiguous longitudinal links require a versioned override in `config/concordances/`.

## Provenance

Pair statistics and vacancy/cut-off data are different raw files, so a canonical row records both raw digests:

```text
pair_statistics_source_sha256
placement_source_sha256
```

and a deterministic combined fingerprint:

```text
source_sha256 = SHA256(sorted(unique(raw digests)))
```

The combined digest is a lineage fingerprint. It is not mislabelled as the digest of one raw file.

## Coverage gates

Every ingestion run should produce a year/phase coverage table containing:

- row count;
- distinct institutions;
- distinct courses;
- missingness in vacancies, applicants, first choices, placements and grade fields.

A parser change is not accepted merely because it completes without an exception. Unexpected row-count changes or missingness jumps require inspection against the raw DGES source.

## Commands

```bash
# Registered source plan
poetry run pt-he-pipeline dges-manifest \
  --output data/source_manifests/dges_first_phase.parquet

# Discover and download a standard annual bundle with receipts
poetry run pt-he-pipeline acquire-dges-year \
  --year 2025 \
  --raw-root data/raw

# Parse pair statistics and capacity/cut-off sources
poetry run pt-he-pipeline parse-pair-pdf \
  --source data/raw/dges/2025/StCEs25.pdf \
  --year 2025 --phase 1 \
  --output data/interim/dges/2025/pair_statistics.parquet

poetry run pt-he-pipeline parse-placement \
  --source data/raw/dges/2025/Fase1a25.pdf \
  --year 2025 --phase 1 \
  --output data/interim/dges/2025/placements.parquet

# Reconcile the two source families
poetry run pt-he-pipeline build-cna-pairs \
  --pair-statistics data/interim/dges/2025/pair_statistics.parquet \
  --placements data/interim/dges/2025/placements.parquet \
  --output data/processed/dges/cna_pairs_2025.parquet

poetry run pt-he-pipeline coverage-report \
  --source data/processed/dges/cna_pairs_2025.parquet \
  --output results/coverage/cna_pairs_2025.csv
```

## Current release boundary

The repository does not bundle DGES provider bytes. This environment could verify the public source structure but could not reliably download the historical binary archive into the working container. Version 0.2 therefore ships the parsers, manifest, concordance policy, provenance checks and tests, but **does not claim that the 1997–2026 empirical panel has already been executed**.
