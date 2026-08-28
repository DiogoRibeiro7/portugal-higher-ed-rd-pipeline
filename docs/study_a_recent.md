# Study A: recent-window baseline, 2023-2026

## Purpose

Version 0.3 introduces the first empirical result for Study A using the compact
first-phase tables published by DGES. It is deliberately narrower than the
registered long-run study. The aim is to establish what the most recent four
competition years say before the full 1997-2026 programme-level panel is frozen.

The source is **Quadro V — Vagas, candidatos em 1.ª opção, colocados e vagas
sobrantes por área de estudos** from the official first-phase result note for each
year. The curated panel contains all 23 published broad study areas in each year,
not only the STEM rows.

## Provenance boundary

The execution container could not reliably retrieve every historical provider
binary. The 2023-2026 compact tables were therefore transcribed from the published
official tables and independently reconciled to their national totals.

This is not presented as a raw-provider receipt. Instead:

- `data/source_manifests/dges_study_a_recent.csv` records the official source URL
  and table for every year;
- `data/curated/dges/first_phase_area_2023_2026.csv` contains the published
  aggregate values;
- the analysis refuses to run unless the broad-area sums match the official
  national vacancies, candidates and placements exactly;
- `results/study_a/recent_window_receipt.json` hashes the curated inputs,
  analysis code, study configuration and result tables.

Provider bytes remain a separate provenance level and are not claimed to be
bundled in this release.

## Crosswalk

The compact DGES notes use broad Portuguese study-area labels rather than an
ISCED-F column. For this recent-window baseline, the registered broad STEM groups
are constructed deterministically as follows.

| Registered group | Published DGES areas |
|---|---|
| 05 — Natural sciences, mathematics and statistics | Ciências da Vida; Ciências Físicas; Matemática e Estatística |
| 06 — Information and communication technologies | Informática |
| 07 — Engineering, manufacturing and construction | Engenharia e Técnicas Afins; Indústrias Transformadoras; Arquitetura e Construção |

Historical spelling variants such as `Arquitectura`/`Arquitetura` are normalised
only for matching. The original source label remains in the curated data.

The seven source areas are retained in the outputs. The three registered groups
are therefore an additional aggregation layer rather than a replacement for the
published categories.

## Validation

For every year, the following identities are required:

\[
\sum_g V_{gt}=V_t,
\qquad
\sum_g A^{(1)}_{gt}=A_t,
\qquad
\sum_g P_{gt}=P_t,
\]

where the candidate identity is valid because each valid CNA candidate has one
first choice. The 23-area coverage must also be stable after spelling
normalisation.

The source note warns that remaining vacancies need not equal initial vacancies
minus placements because additional places can be created during allocation.
Consequently, the pipeline validates the published remaining-vacancy total but
does not impose the false identity

\[
V_t-P_t=U_t.
\]

## Available estimands

The compact table supports:

\[
O_{gt}=\frac{P_{gt}}{V_{gt}},
\qquad
F_{gt}=\frac{A^{(1)}_{gt}}{V_{gt}},
\qquad
S_{gt}=\frac{P_{gt}}{P_{\cdot t}}.
\]

It does **not** report all applications by broad area. Therefore the registered
applicants-per-vacancy measure is not manufactured by treating first-choice
candidates as total applicants. That estimand remains pending the detailed
programme-level source.

## Results

For all registered STEM fields combined:

| Year | Vacancies | First-choice candidates | Placements | Occupancy | Placement share |
|---:|---:|---:|---:|---:|---:|
| 2023 | 18,355 | 15,082 | 14,984 | 81.63% | 30.31% |
| 2024 | 18,396 | 15,716 | 15,365 | 83.52% | 30.75% |
| 2025 | 18,471 | 12,967 | 13,183 | 71.37% | 30.03% |
| 2026 | 18,730 | 15,103 | 15,181 | 81.05% | 30.37% |

The 2025 fall is large, but it is followed by a strong 2026 rebound. Relative to
2023, the 2026 aggregate placement count is **1.3% higher**, while its share of all
first-phase placements is almost unchanged.

The endpoint comparison is heterogeneous:

| Component | 2023 placements | 2026 placements | Change |
|---|---:|---:|---:|
| Natural sciences, mathematics and statistics | 3,721 | 3,557 | -4.4% |
| Information and communication technologies | 1,447 | 1,312 | -9.3% |
| Engineering, manufacturing and construction | 9,816 | 10,312 | +5.1% |
| **All registered STEM** | **14,984** | **15,181** | **+1.3%** |

The underlying DGES areas matter. `Engenharia e Técnicas Afins` itself rises from
8,233 placements in 2023 to 8,557 in 2026 (+3.9%). Within science, `Ciências da
Vida` and `Ciências Físicas` are lower in 2026 than in 2023, while `Matemática e
Estatística` is higher.

## What this does and does not establish

The recent four-year window does not support describing the aggregate pattern as
one uninterrupted decline. It also does not establish that a longer-run decline
is absent. Four observations are insufficient for the registered long-run trend
claim, and 2025 is clearly an unusual trough in overall CNA participation.

Accordingly, the release status for Proposition 1 is:

> **Recent-window evidence: heterogeneous and non-monotonic. Long-run proposition:
> not yet adjudicated.**

The next Study A release must add the historical programme-level panel,
demographic denominators, field-crosswalk checks across programme reforms and the
pre-registered long-run trend and structural-break diagnostics.
