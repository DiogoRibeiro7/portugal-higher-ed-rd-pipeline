# Reproducibility and provenance

## Immutable raw layer

Raw downloads are never edited in place. Each acquisition writes a JSON receipt next to the file containing:

- source URL;
- retrieval time (UTC);
- size in bytes;
- SHA-256 digest.

Processed rows carry the exact raw digests needed to reconstruct their lineage.

## Curated publication-table layer

A small public aggregate table can be committed under `data/curated/` when the
published values are needed for a transparent baseline but the raw provider bytes
are not bundled. Such a table is never labelled as raw data or assigned a provider
SHA-256 digest. It must record the official source document and reconcile to
published control totals.

The v0.3.0 and v0.3.1 Study A publication-table layers follow this rule. Their
analysis receipts hash the curated CSVs, source manifests, configurations, code,
tests and numerical result tables. The v0.3.1 coverage output also makes the missing
2019 broad-area source year machine-visible. This establishes the lineage of the
repository artefacts while leaving the stronger raw-provider receipt claim explicitly
false.

A source-coverage gap is never converted to a numeric observation. In particular,
the medium-run Study A figures reindex the expected 2017-2026 calendar and leave 2019
missing, while year-on-year change is suppressed at 2020 rather than treating the
2018-to-2020 movement as a one-year change.

The v0.3.2 demographic sensitivity follows the same separation. The INE/PORDATA
15-24 series is committed as a curated statistical input with its source and update
date. Dividing that age band by ten is a deterministic derived proxy and is labelled
as such. It is not treated as provider-supplied age-18 data, and it cannot fill the
missing 2019 field observation. The demographic receipt binds the input series,
configuration, implementation, tests and numerical outputs.

The v0.3.3 matched-course pilot applies the same rule to two official DGES `StatsCurso`
comparative publications. Provider PDF bytes are not bundled, so the committed 92-row
source table is explicitly a curated transcription. The two publications overlap in
2019. Before deduplication, the pipeline verifies exact equality of all registered
counts and grade measures for each of the 23 repeated institution-course records. The
69-row analytical panel is therefore built only after a cross-vintage consistency gate.

## Multiple-source canonical rows

The CNA pair panel combines information from pair-statistics sheets and vacancy/placement tables. These are separate provider files. The canonical row therefore retains:

```text
pair_statistics_source_sha256
placement_source_sha256
```

and adds a deterministic lineage fingerprint:

```text
source_sha256 = SHA256(sorted(unique(raw digests)))
```

The fingerprint binds the raw inputs but is not described as a provider-file hash.

## Deterministic transformations

- Parsers return explicit schemas.
- Missing values are preserved as missing.
- Derived ratios use well-defined zero-denominator behaviour.
- Duplicated placement counts across DGES source families must agree exactly.
- Institution and programme concordances are versioned.
- Fuzzy programme merges are not automatic.
- Random procedures must accept and record a seed.

## Data-vintage discipline

The 2026 CNA series can change as later phases are published. The project therefore records both the competition phase and retrieval date. A first-phase analysis is not silently updated with second- or third-phase data.

Mobility files create a second vintage problem because one annual document can reproduce both the current and previous competition year. Mobility rows therefore record `source_document_year`. When duplicate copies are available, the matrix in its own competition year's document is preferred, and later comparative copies are retained only as auditable fallbacks.

## Historical geography

Legacy mobility origins can be CAE/GAES access areas rather than districts. These labels are preserved as `access_area`. They are not coerced into district identifiers merely to increase the diagonal share. Any same-district statistic must report the proportion of flows whose origin definition is genuinely comparable.

## External ranking data

Ranking data may be proprietary or subject to restrictive reuse terms. Such inputs are not committed by default. Their local path and digest can be recorded in the analysis manifest so results remain auditable without redistributing the dataset.

## Release checklist

Before an empirical release:

1. freeze source receipts;
2. validate all canonical data contracts;
3. run unit and parser tests;
4. compare row counts and missingness with the prior accepted parser vintage;
5. run `ruff` and `mypy`;
6. execute the full analysis from a clean environment;
7. record row counts and missingness by source/year;
8. compile the paper without unresolved references;
9. archive the result manifest and code commit hash.
