# Study B multi-course extraction gate

## Purpose

Version 0.3.4 extends the matched-course pilot to the five programmes frozen before full extraction:

- 9081 — Economia;
- 9119 — Engenharia Informática;
- 9147 — Gestão;
- 9219 — Psicologia;
- 9500 — Enfermagem.

The empirical layer must be built from the official DGES `StatsCurso` comparative first-phase tables for 2019 and 2020. No programme may be added or removed after inspecting the demand/grade association results.

## Source contract

The registered documents are:

- `StatsCurso19.pdf`, carrying 2018 and 2019 observations;
- `StatsCurso20.pdf`, carrying 2019 and 2020 observations.

The duplicated 2019 observations are an internal source-reconciliation test. For every programme-establishment pair present in both documents, all registered measures must agree before the contemporary document is retained as the canonical source row.

The required row schema is the same as the course-9119 pilot:

```text
source_document_year
source_url
source_pages
source_section
source_type
provider_bytes_bundled
year
programme_code
programme_name
degree
institution_code
institution_name
vacancies
applicants
first_choice_applicants
placements
first_choice_placements
last_placed_general_contingent_grade
mean_application_grade_placed
mean_entrance_exam_grade_placed
mean_secondary_grade_placed
```

## Selection order

The extraction and analysis deliberately use this order:

1. extract every registered programme-establishment observation from both source vintages;
2. reconcile duplicated 2019 observations;
3. identify programme-establishment units offered in all three years using source coverage only;
4. enforce the frozen minimum of six stable establishments per programme;
5. calculate demand and occupancy measures;
6. report modelling attrition caused by zero demand or unavailable grade outcomes;
7. fit programme-by-year demand/grade associations only on the model-complete subset.

This ordering prevents outcome availability from silently redefining the stable-offering population.

## Fail-closed build

Run:

```bash
poetry run python scripts/build_study_b_multi_course.py
```

The builder refuses to run until the registered source table exists at:

```text
data/curated/dges/study_b_multi_course_source_rows.csv
```

It does not substitute the existing 9119 pilot for missing programmes, relax the programme registry, impute missing source rows, or lower the stable-establishment gate.

When the source table is complete, the builder writes reconciliation, coverage, stable-panel, model-attrition, model-panel, programme-year association, and association-summary artefacts under `results/study_b/`.

## Current provenance boundary

The repository currently registers the ten programme-document combinations in `data/source_manifests/dges_study_b_multi_course.csv`. The 9119 rows already exist from v0.3.3. The other four programmes remain `pending_registered_extraction` until the official source content can be recovered and transcribed with the same provenance discipline.

No multi-course empirical result should be reported before that boundary is crossed.
