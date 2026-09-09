# Portuguese Higher Education Demand, Regionality, and R&D Pipeline

A reproducible empirical study of three claims about Portuguese higher education and the research workforce:

1. **Science and engineering placements are declining.**
2. **University choice is strongly regional and demand pressure explains most differences in entry grades; ranking information adds little once the relevant structure is accounted for.**
3. **High-performing R&D units exposed to a weakening education pipeline may face future capacity constraints.**

The repository is deliberately neutral. It does not begin by accepting or rejecting any claim. Each proposition is translated into measurable quantities, uncertainty is reported, and descriptive, predictive, associational and causal statements are kept separate.

## Research map

| Study | Main question | Primary unit | Core outcomes |
|---|---|---|---|
| A — STEM placements | Is there a sustained fall in science and engineering demand and placement? | programme × institution × year | applicants, first choices, placements, vacancies, occupancy, placement share |
| B — Regionality, demand and entry grades | How much do geography and demand pressure account for student choices and entry grades? | origin area × destination district; programme × institution × year | first-choice flows, placement flows, applicants/vacancy, mean and cut-off grades |
| C — R&D pipeline | Are strong R&D units increasingly exposed to declining feeder pipelines? | R&D unit × host institution × field × year | entrants, graduates, MSc/PhD pipeline, researchers, FCT evaluation and unit size |

## Pipeline architecture and provenance

![Pipeline provenance architecture](docs/diagrams/rendered/pipeline_provenance.svg)

The repository is organized around a provenance chain rather than a service architecture: official sources are acquired or transcribed under frozen source contracts, bound to receipts and deterministic lineage, transformed into canonical data, rebuilt into public Study A and Study B evidence, and then compiled into the manuscript and release-validation layer.

The diagram also marks the reproducibility boundary explicitly. The provider-specific ranking model depends on a non-redistributed private ranking panel, and Study C is a separate downstream research track; neither is part of the v0.3.4 `make empirical-public` rebuild. See [`docs/architecture.md`](docs/architecture.md) for the full architecture and release boundary.

## Key design choices

- **CNA first phase is the primary access series.** Later phases are sensitivity analyses because they mix unfilled capacity and reallocation dynamics.
- **STEM is not treated as one homogeneous block.** Natural sciences/mathematics/statistics, ICT, and engineering/manufacturing/construction are reported separately before aggregation.
- **Counts and shares are both reported.** A fall in placements can reflect demography, overall participation, capacity, or field-specific demand.
- **Regionality is measured from origin–destination flows**, using first preference as the cleaner preference measure and actual placement as a constrained outcome.
- **Historical origin geography is preserved.** Older CAE/GAES access areas are not silently relabelled as districts; comparable-flow coverage accompanies district-diagonal measures.
- **Applicants per vacancy is descriptive/predictive, not automatically causal.** Entry grades are order-statistic outcomes, so a strong relation is partly structural.
- **Rankings are secondary.** The project can ingest licensed or user-supplied QS/THE/ARWU-style series but does not redistribute proprietary ranking data.
- **FCT evaluation ratings are called performance ratings, not “impact” measures.** Bibliometric impact is a separate construct and requires separate data.
- **Pipeline risk is not reduced to one arbitrary index in the primary analysis.** Entrants, graduates, doctoral flow and research staffing are reported component by component. A composite is exploratory only.

## Official data backbone

The project is built around public Portuguese sources:

- **DGES — Concurso Nacional de Acesso (CNA):** historical statistics, institution/programme pairs, first-phase placements, vacancies, applicants, first choices, entry grades, and geographic mobility tables.
- **DGEEC — RAIDES and education statistics:** enrolled students, first-time entrants and graduates by cycle and field.
- **FCT — R&D Unit evaluations and Atlas:** unit host institutions, scientific domains, integrated researchers, performance ratings and funding context.
- **DGEEC — IPCTN / science and technology statistics:** R&D personnel and institutional research activity.
- **INE demographic series:** exact age-18 population from indicator `0001223`, with the broader INE/PORDATA 15–24 series retained as a secondary demographic sensitivity.
- **Optional ranking inputs:** user-supplied historical ranking series with provenance and licence recorded.

See [`docs/data_sources.md`](docs/data_sources.md), [`docs/dges_ingestion.md`](docs/dges_ingestion.md) and [`config/source_registry.yml`](config/source_registry.yml).

## Repository structure

```text
.
├── config/                  # frozen study, source and concordance registries
├── data/                    # raw/interim/processed data plus source manifests
├── docs/                    # research design, data contracts and limitations
├── paper/                   # LaTeX paper
├── prompts/                 # reproducible research prompts / hand-off notes
├── scripts/                 # acquisition and panel-building entry points
├── src/pt_he_pipeline/      # typed Python package
└── tests/                   # unit and contract tests
```

## Quick start

```bash
poetry install
poetry run pytest
poetry run ruff check .
poetry run mypy src
```

Build the registered DGES source-vintage plan:

```bash
poetry run pt-he-pipeline dges-manifest \
  --output data/source_manifests/dges_first_phase.parquet
```

Acquire the standard source bundle for a historical year. Every download receives a SHA-256 receipt:

```bash
poetry run pt-he-pipeline acquire-dges-year \
  --year 2025 \
  --raw-root data/raw
```

The two main source families are parsed separately and reconciled only after parsing:

```bash
poetry run pt-he-pipeline parse-pair-pdf \
  --source data/raw/dges/2025/StCEs25.pdf \
  --year 2025 --phase 1 \
  --output data/interim/dges/2025/pair_statistics.parquet

poetry run pt-he-pipeline parse-placement \
  --source data/raw/dges/2025/Fase1a25.pdf \
  --year 2025 --phase 1 \
  --output data/interim/dges/2025/placements.parquet

poetry run pt-he-pipeline build-cna-pairs \
  --pair-statistics data/interim/dges/2025/pair_statistics.parquet \
  --placements data/interim/dges/2025/placements.parquet \
  --output data/processed/dges/cna_pairs_2025.parquet
```

A disagreement in the duplicated placement count is a hard error. It is not resolved by silently preferring one source.

Generate a year/phase coverage report:

```bash
poetry run pt-he-pipeline coverage-report \
  --source data/processed/dges/cna_pairs_2025.parquet \
  --output results/coverage/cna_pairs_2025.csv
```

## Canonical estimands

### Study A — STEM placements

For field group \(g\) and year \(t\):

\[
S_{gt}=\frac{\text{placed}_{gt}}{\text{placed}_{\cdot t}},
\qquad
O_{gt}=\frac{\text{placed}_{gt}}{\text{vacancies}_{gt}},
\qquad
D_{gt}=\frac{\text{applicants}_{gt}}{\text{vacancies}_{gt}}.
\]

The primary question concerns the trend in **both the absolute number and share of placements**. Demographic-normalised rates are reported alongside them.

#### Medium-run evidence and demographic normalisations

The medium-run layer uses the complete official broad-area first-phase table for
2017, 2018 and 2020-2026. The official 2019 first-phase archive has now been audited:
it lists summary, course, establishment, mobility, cut-off and programme-pair resources,
but no comparable complete broad-area table. **No 2019 field observation is imputed,
interpolated or reconstructed.**
Every observed year retains all 23 source areas and reconciles exactly to the published
national vacancies, valid candidates, placements and published remaining vacancies before any STEM aggregation.

The endpoint comparison is already informative:

| Component | 2017 placements | 2026 placements | Change |
|---|---:|---:|---:|
| 05 — Natural sciences, mathematics and statistics | 3,816 | 3,557 | -6.8% |
| 06 — Information and communication technologies | 820 | 1,312 | +60.0% |
| 07 — Engineering, manufacturing and construction | 9,290 | 10,312 | +11.0% |
| **All registered STEM** | **13,926** | **15,181** | **+9.0%** |

Absolute STEM placements rise between the endpoints, while the STEM share of all
first-phase placements moves from 31.01% to 30.37% (-0.64 percentage points). A
descriptive log-linear fit across the nine source-locked years corresponds to +0.46%
placements per calendar year, but with very low explanatory power (R² = 0.050). The
frozen sensitivity excluding 2020-2021 gives +0.75% per year. These lines summarise
the observed administrative path; they are not sampling-inference or causal estimates.

The component paths matter more than the all-STEM aggregate. Group 05 trends down,
ICT expands strongly from its 2017 base, and group 07 ends above 2017. The result is
therefore not consistent with describing **absolute first-phase STEM placements since
2017** as one sustained decline. It still does not adjudicate the registered 1997-2026
programme-level proposition because the broad-area layer has a 2019 field-composition
gap and lacks programme-level total applications.

The preferred demographic denominator is now the source-locked INE population aged
exactly 18, indicator `0001223`, using Portugal (`PT`), total sex (`T/HM`) and age code
`224`. Competition year \(t\) uses population year \(t-1\), so the released 2017–2026
comparison uses population values for 2016–2025. INE documents a methodology change
between the 2020 and 2021 population estimates, which is carried as a comparability
caveat rather than interpreted automatically as demographic change.

The exact-age and historical broad-cohort results differ materially:

| Component | Raw placement change | Exact age-18 rate change | 15–24/10 proxy rate change |
|---|---:|---:|---:|
| 05 — Natural sciences, mathematics and statistics | -6.8% | -6.7% | -13.3% |
| 06 — Information and communication technologies | +60.0% | +60.1% | +48.7% |
| 07 — Engineering, manufacturing and construction | +11.0% | +11.1% | +3.2% |
| **All registered STEM** | **+9.0%** | **+9.1%** | **+1.3%** |

The age-18 population is almost unchanged between the endpoint population references
(110,479 in 2016 and 110,376 in 2025), so exact-age normalisation leaves the raw
all-STEM increase essentially intact. By contrast, the 15–24 population rises by about
7.6%, which strongly attenuates the broad-proxy rate. The proxy therefore measures
broad young-adult population scale, not the registered entry-age cohort. It is retained
as a secondary sensitivity rather than promoted to the preferred denominator.

See [`docs/study_a_medium_run.md`](docs/study_a_medium_run.md),
[`docs/study_a_demography.md`](docs/study_a_demography.md), and the receipt-bound
outputs in [`results/study_a/`](results/study_a/).

Reproduce the medium-run layer and both demographic normalisations with:

```bash
poetry run python scripts/build_study_a_medium_run.py
poetry run python scripts/build_study_a_age18.py
poetry run python scripts/build_study_a_demographic.py
```

The earlier 2023-2026 v0.3.0 baseline is retained as a separately reproducible layer:

```bash
poetry run python scripts/build_study_a_recent.py
```

### Study B — geography and demand

For the subset of origin areas that are directly comparable to destination districts, regionality is summarised first by the diagonal share of the first-choice matrix:

\[
R_t=\frac{\sum_d F_{ddt}}{\sum_{d,k}F_{dkt}}.
\]

The coverage of this comparable-origin subset is reported explicitly. Entropy, mutual information and a gravity-style model supplement the diagonal share.

For grades, nested models compare programme/year structure with and without demand pressure and ranking information. The target is the incremental explanatory and predictive contribution, not a causal coefficient by default.

#### v0.3.3 matched-course demand/selectivity pilot

The first programme-level pilot holds **DGES course code 9119 — Engenharia Informática
[Licenciatura]** fixed across the same 23 institutions in 2018, 2019 and 2020. Two
consecutive official `StatsCurso` tables overlap in 2019; all duplicated vacancies,
applicant counts, placements and grade measures must agree exactly before the 69-row
canonical panel is built. The source layer therefore contains 92 rows and uses the
23 duplicated 2019 observations as a hard cross-vintage reconciliation gate.

The primary demand variable is

\[
D_{jt}=\frac{\text{total applicants}_{jt}}{\text{vacancies}_{jt}},
\]

with first-choice applicants per vacancy retained as a secondary pressure measure.
Within this exact matched course, a one-predictor model using `log(D)` accounts for
55.9%-74.3% of the cross-institution variation in the general-contingent cut-off across
the three years, and 49.8%-76.6% of the variation in the mean application grade of
placed candidates. That is a strong association, but not a near-complete explanation
in every year.

A pooled year-plus-demand description reaches \(R^2=0.674\) for the cut-off and
\(R^2=0.679\) for the mean placed grade. Institution fixed effects account for much
of the persistent cross-institution structure; adding contemporaneous demand on top of
institution and linear-year structure raises \(R^2\) by 0.020 and 0.018 respectively.
Demand still improves leave-one-year-out prediction: institution-plus-year cut-off RMSE
falls from 9.10 to 7.49 grade points, and mean-grade RMSE from 6.51 to 5.13.

This is deliberately a **matched-course pilot**, not an estimate for all Portuguese
higher education. Rankings and regionality are not included yet. Its purpose is to
validate the programme-level contract and establish which comparisons can be scaled
without changing the estimand. See
[`docs/study_b_course_pilot.md`](docs/study_b_course_pilot.md).

Rebuild the pilot with:

```bash
poetry run python scripts/build_study_b_course9119_pilot.py
```

### Study C — research pipeline

For each feeder field and host institution, the project tracks:

\[
\text{first-time entrants}
\rightarrow
\text{graduates}
\rightarrow
\text{masters}
\rightarrow
\text{doctorates}
\rightarrow
\text{research personnel}.
\]

Lagged exposure is then linked to R&D-unit characteristics. Where the historical depth is insufficient to identify downstream consequences, the result is labelled **prospective vulnerability**, not a demonstrated future effect.

## Reproducibility

Every downloaded source is stored with a receipt containing its URL, retrieval timestamp, byte size and SHA-256 digest. Canonical CNA rows bind the separate pair-statistics and vacancy/placement digests into one deterministic lineage fingerprint. Raw files are immutable inputs; transformations write new artefacts. See [`docs/reproducibility.md`](docs/reproducibility.md).

## Current status — v0.3.4

Study A now contains the source-locked 2023-2026 recent baseline, the 2017/2018 and
2020-2026 medium-run broad-area panel, the exact age-18 demographic normalisation, and
the older broad-cohort proxy sensitivity. Raw registered STEM placements are 9.0%
higher in 2026 than in 2017, their placement share is 0.64 percentage points lower,
and the exact age-18-normalised endpoint rate is 9.1% higher. The broad 15–24/10 proxy
gives only +1.3% and is retained as a weaker secondary sensitivity. The registered
1997-2026 programme-level proposition remains open.

Version 0.3.3 adds the first programme-level Study B evidence: a balanced 23-institution
matched panel for course 9119 in 2018-2020, constructed from two overlapping official
DGES comparative-course tables. The duplicated 2019 observations reconcile exactly.
Applicants per vacancy are strongly associated with both cut-off and mean placed grades,
but the amount explained varies materially by year and persistent institution structure
accounts for a large share of the between-institution differences. Demand also improves
leave-one-year-out prediction in this pilot.

The v0.3.4 release boundary consolidates the source-locked Study A evidence and the publicly reproducible Study B layers without changing their estimands. `make empirical-public` is the canonical public rebuild entry point. The provider-specific ranking model remains outside that public rebuild because it requires the non-redistributed ranking panel, and Study C remains a separate downstream research track.

The next evidence gates are extending historical coverage where programme comparability can be demonstrated and completing the remaining Study C work without weakening the current source and reproducibility contracts. The exact age-18 denominator is no longer an unresolved acquisition gate.

## Licence

Code is released under the MIT Licence. Data remain subject to the terms of their original providers.
