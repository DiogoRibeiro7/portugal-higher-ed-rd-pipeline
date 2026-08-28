# Data contracts

## `cna_pairs`

Canonical course–institution–year table.

| Column | Type | Required | Meaning |
|---|---|---:|---|
| `year` | integer | yes | CNA year |
| `phase` | integer | yes | competition phase; primary analysis uses 1 |
| `institution_id` | string | yes | stable/concorded institution identifier |
| `course_id` | string | yes | stable/concorded course identifier |
| `source_institution_id` | string | yes | institution identifier as published |
| `source_course_id` | string | yes | course identifier as published |
| `institution_name` | string | yes | source label |
| `course_name` | string | yes | source label |
| `field_code` | string | no | ISCED-F 2013 field |
| `district` | string | no | institution district |
| `vacancies` | integer | yes | places offered |
| `applicants` | integer | yes | applicants |
| `first_choice_applicants` | integer | no | applicants listing pair first |
| `placements` | integer | yes | placed students |
| `mean_application_grade_placed` | float | no | mean application grade of placed students |
| `last_placed_general_contingent_grade` | float | no | last placed grade in general contingent |
| `pair_statistics_source_sha256` | string | yes | hash of the pair-statistics source |
| `placement_source_sha256` | string | yes | hash of the vacancy/placement source |
| `source_sha256` | string | yes | deterministic lineage fingerprint binding the raw digests |

## `mobility_flows`

| Column | Type | Meaning |
|---|---|---|
| `year` | integer | CNA competition year |
| `source_document_year` | integer | year of the comparative mobility document used |
| `flow_type` | string | `first_choice` or `placement` |
| `origin_area` | string | published district, autonomous region or legacy CAE/GAES access area |
| `origin_area_type` | string | `district`, `autonomous_region` or `access_area` |
| `destination_district` | string | first-choice or placement district |
| `count` | integer | applicants/placed students in the cell |
| `source_sha256` | string | hash of raw source |

## `education_pipeline`

| Column | Type | Meaning |
|---|---|---|
| `academic_year` | string | source academic year |
| `institution_id` | string | harmonised institution |
| `field_code` | string | ISCED-F field |
| `stage` | string | entrant / graduate / MSc / PhD / other registered stage |
| `count` | float | headcount or FTE, as explicitly labelled |
| `measure_type` | string | `headcount` or `fte` |
| `source_sha256` | string | source hash |

## `rd_units`

| Column | Type | Meaning |
|---|---|---|
| `evaluation_wave` | string | FCT evaluation wave |
| `unit_id` | string | FCT unit identifier |
| `unit_name` | string | official name |
| `rating` | string | published evaluation category |
| `scientific_domain` | string | FCT domain/panel |
| `host_institution_id` | string | harmonised host institution |
| `integrated_researchers` | float | unit size where published |
| `funding_eur` | float | funding where published and comparable |
| `source_sha256` | string | source hash |

## `rankings` — optional

| Column | Type | Meaning |
|---|---|---|
| `year` | integer | ranking vintage/publication year |
| `provider` | string | ranking provider |
| `institution_id` | string | harmonised institution |
| `rank` | float | numerical rank if published |
| `rank_band` | string | band if exact rank is not published |
| `score` | float | provider score if published |
| `published_date` | date | publication date |
| `provenance` | string | provider/source reference |

A rank band must not be replaced by its midpoint in the primary analysis without an explicit sensitivity label.

## `study_a_recent_area` — curated recent-window baseline

This is a small, publication-table transcription used only for the 2023-2026
Study A baseline. It is not the canonical long-run course panel.

| Column | Type | Meaning |
|---|---|---|
| `year` | integer | CNA competition year |
| `area` | string | published DGES broad-area label |
| `vacancies` | integer | first-phase places offered |
| `first_choice_applicants` | integer | valid candidates naming the area in first choice after aggregation |
| `placements` | integer | first-phase placed students |
| `remaining_vacancies` | integer | published places remaining after the first phase |
| `source_document` | string | official result-note filename |
| `source_table` | string | `Quadro V` |

The 23 published areas must reconcile exactly to the national vacancies,
candidates and placements for every year. Remaining vacancies are checked against
the published total, but are not required to equal vacancies minus placements
because additional places can be created during allocation.

## `study_a_medium_run_area` — source-locked broad-area extension

This contract extends the publication-table layer to the observed years 2017, 2018
and 2020-2026. It uses the same count columns as `study_a_recent_area`, but the
`source_table` field is vintage-aware: `Quadro XII` is registered for 2017 and
`Quadro V` for the later locked vintages.

| Column | Type | Meaning |
|---|---|---|
| `year` | integer | CNA competition year |
| `area` | string | published broad-area label |
| `vacancies` | integer | first-phase places offered |
| `first_choice_applicants` | integer | valid candidates contributing one first choice |
| `placements` | integer | first-phase placed students |
| `remaining_vacancies` | integer | published places remaining after the first phase |
| `source_document` | string | official result-note filename |
| `source_table` | string | registered broad-area table identifier (`Quadro V` or `Quadro XII`) |

The committed file must contain exactly 23 rows for every source-locked year and no
row for a year whose complete table is not source-locked. In v0.3.2, 2019 is an
explicit missing source year after an audit of the official standard first-phase archive. Every observed year must reconcile to national
vacancies, candidates and placements before any analysis output is eligible.

## `study_a_medium_run_coverage`

| Column | Type | Meaning |
|---|---|---|
| `year` | integer | expected calendar year in the frozen 2017-2026 window |
| `observed` | boolean | whether a complete source-locked broad-area table is present |
| `status` | string | `source_locked` or `not_source_locked` |

Coverage is an analytical output, not metadata hidden in prose. Missing source years
are therefore mechanically visible to downstream code and figures.

## `study_a_demographic_population` — broad-cohort sensitivity input

This input is a sensitivity denominator, not the registered exact age-18 series.

| Column | Type | Meaning |
|---|---|---|
| `population_year` | integer | calendar year of the demographic estimate |
| `population_15_24` | integer | INE resident population aged 15-24 disseminated by PORDATA |
| `source_entity` | string | source statistical entity; `INE` |
| `dissemination` | string | dissemination service; `PORDATA` |
| `source_url` | string | registered public source |
| `source_last_updated` | date string | source update date |

For an observed CNA competition year \(t\), the sensitivity uses population year
\(t-1\) and defines

\[
C^{proxy}_t = \frac{N_{15:24,t-1}}{10}.
\]

`C_proxy` is an average single-year cohort equivalent. It must never be labelled as
the population aged exactly 18. Missing CNA field observations remain missing after
normalisation; the denominator cannot be used to reconstruct 2019 placements.

## `study_b_course_comparison_source` — matched-course source layer

Version 0.3.3 uses a narrow source contract for the first programme-level pilot. Each
row is one publication-document × competition-year × institution observation for DGES
course code 9119. The same 2019 observation appears in both the 2019 and 2020
comparative publications and is deliberately retained twice at this layer.

| Column | Type | Meaning |
|---|---|---|
| `source_document_year` | integer | comparative DGES publication vintage |
| `year` | integer | CNA competition year |
| `programme_code` | string | published course code; fixed at `9119` |
| `institution_code` | string | published institution/establishment code |
| `vacancies` | integer | initial first-phase vacancies |
| `applicants` | integer | total applicants to the pair |
| `first_choice_applicants` | integer | applicants listing the pair first |
| `placements` | integer | total placements |
| `first_choice_placements` | integer | placed candidates whose first choice is the pair |
| `last_placed_general_contingent_grade` | float | general-contingent cut-off on the 0-200 scale |
| `mean_application_grade_placed` | float | mean application grade of placed candidates |
| `mean_entrance_exam_grade_placed` | float | published mean entrance-exam grade |
| `mean_secondary_grade_placed` | float | published mean secondary-school grade |
| `source_url` | string | official DGES comparative-course PDF |
| `provider_bytes_bundled` | boolean | false for this curated source layer |

The overlap year is a hard validation gate: every measure above must match exactly
across both source documents for every institution before canonicalisation.

## `study_b_course9119_panel` — canonical pilot panel

The canonical table contains exactly 23 institutions × 3 years = 69 rows. It adds:

| Column | Type | Meaning |
|---|---|---|
| `applicants_per_vacancy` | float | total applicants divided by initial vacancies |
| `first_choice_pressure` | float | first-choice applicants divided by vacancies |
| `occupancy_rate` | float | placements divided by vacancies; can exceed 1 because of tie places |
| `year_offset` | integer | calendar year minus 2019 |

No ranking, regionality or ISCED cross-programme generalisation is attached to this
pilot panel.

