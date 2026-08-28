# Release validation — v0.3.3

Date: 2026-08-26

## Scientific scope

- The three registered propositions remain empirical questions, with no preferred conclusion.
- Study A continues to separate absolute placements, placement share, first-choice pressure,
  field composition and demographic scale.
- Study B now contains a narrow matched-course empirical pilot before any system-wide demand,
  regionality or ranking claim is evaluated.
- Descriptive, predictive, associational and causal language remains separated.
- No p-values or sampling-confidence statements are attached to administrative population
  counts or to the matched-course descriptive regressions.
- Rankings are not evaluated in this release.
- Study C remains registered but has no empirical result yet.

## v0.3.3 empirical boundary

The new Study B pilot holds the course exactly fixed at DGES code `9119`,
`Engenharia Informática [Licenciatura]`, and follows the same 23 institutions in 2018,
2019 and 2020. It is therefore a matched-course comparison rather than a pooled comparison
of unlike degrees.

The curated source layer contains **92 rows** transcribed from two official DGES comparative
course publications:

- the 2019 comparative publication supplies 2018 and 2019 observations;
- the 2020 comparative publication supplies 2019 and 2020 observations.

The 23 observations for 2019 are deliberately present twice at source level. Every registered
measure must match exactly across the two publications before canonicalisation. Only after that
check are the duplicate 2019 observations collapsed, producing a balanced canonical panel of
**69 rows = 23 institutions × 3 years**.

Provider PDF bytes are not bundled in this runtime. The release therefore records curated
published values and official source URLs, and it does not manufacture provider-file hashes.

## Study A status retained from v0.3.2

The source-locked broad-area series still observes 2017, 2018 and 2020-2026; the comparable
2019 broad-area field table remains missing and is not imputed.

Between the observed endpoints 2017 and 2026:

| Component | Raw placement change | Broad-cohort-proxy rate change |
|---|---:|---:|
| 05 — Natural sciences, mathematics and statistics | -6.8% | -13.3% |
| 06 — Information and communication technologies | +60.0% | +48.7% |
| 07 — Engineering, manufacturing and construction | +11.0% | +3.2% |
| **All registered STEM** | **+9.0%** | **+1.3%** |

The all-STEM share of national first-phase placements moves from 31.01% to 30.37%, a change
of -0.64 percentage points. These margins remain distinct; the release does not reduce them to
one binary statement about decline.

## Study B matched-course result

### Within-year cross-institution association

For total applicants per vacancy, the year-specific log-demand models give:

| Outcome | 2018 R² | 2019 R² | 2020 R² |
|---|---:|---:|---:|
| General-contingent cut-off | 0.647 | 0.559 | 0.743 |
| Mean application grade of placed candidates | 0.498 | 0.620 | 0.766 |

Demand pressure is therefore strongly associated with entry grades in this course, but its
explanatory share is neither constant nor close to complete in every year.

The secondary first-choice-pressure specification is also retained and reported separately. It
is not substituted for total applicants per vacancy.

### Pooled decomposition

With a linear year term only, the cut-off model has R² = 0.058. Adding log applicants per
vacancy raises R² to **0.674**, an incremental **0.616**. For mean placed grade the corresponding
values are 0.105, **0.679** and **0.574**.

Institution fixed effects plus year alone give R² = **0.953** for the cut-off and **0.958** for
mean placed grade. Adding demand raises these to **0.973** and **0.976**, incremental gains of
**0.020** and **0.018**.

This is not interpreted as demand and institution identity being competing causal explanations.
Persistent institution differences and demand share substantial cross-institution structure.

### Leave-one-year-out prediction

For the institution-and-year specification, adding demand improves mean held-out prediction:

| Outcome | Structure-only RMSE | + demand RMSE | Structure-only MAE | + demand MAE |
|---|---:|---:|---:|---:|
| General-contingent cut-off | 9.10 | **7.49** | 7.65 | **6.26** |
| Mean placed grade | 6.51 | **5.13** | 5.63 | **4.32** |

The 2020 vintage coincides with exceptional pandemic-era schooling and assessment conditions.
Year-level movements are therefore not given a causal interpretation. The within-year
cross-institution comparisons are less exposed to a common level shift, but they remain
observational.

## Study B interpretation boundary

The pilot supports the proposition that demand pressure contains substantial information about
entry grades when the programme is held fixed. It does **not** establish that demand explains
entry-grade differences across Portuguese higher education as a whole.

In particular, this release does not yet determine:

- whether the same demand-grade relationship replicates across fields and degrees;
- how much of the association reflects geography, institution reputation or applicant
  composition;
- whether Portuguese universities are predominantly regional;
- whether rankings contain incremental information after demand and location are considered;
- any causal effect of demand, ranking or institution identity on grades.

Those questions require the multi-course programme-by-institution panel registered for the next
stage.

## Study B source and output checks

- Curated source rows: **92**.
- Canonical balanced rows: **69**.
- Institutions in each year: **23**.
- Years: 2018, 2019 and 2020.
- 2019 duplicated source pairs: **23**.
- All duplicated 2019 registered measures reconcile exactly before canonicalisation.
- `results/study_b/course9119_source_reconciliation.csv`: explicit cross-vintage audit.
- `results/study_b/course9119_panel.csv`: canonical matched-course panel.
- `results/study_b/course9119_year_summary.csv`: year-level descriptive summaries.
- `results/study_b/course9119_cross_section_associations.csv`: year-specific associations.
- `results/study_b/course9119_nested_models.csv`: pooled nested specifications.
- `results/study_b/course9119_leave_one_year_out.csv`: held-out predictions by year.
- `results/study_b/course9119_leave_one_year_out_summary.csv`: prediction-error summary.
- `results/study_b/course9119_findings.md`: mechanically derived pilot interpretation.
- `results/study_b/course9119_receipt.json`: content-addressed analysis receipt.

## Provenance checks

All four current analysis receipts were independently re-audited after the final rebuild:

- recent Study A: **13/13** bound file digests plus self-hash passed;
- medium-run Study A: **19/19** bound file digests plus self-hash passed;
- demographic Study A: **15/15** bound file digests plus self-hash passed;
- matched-course Study B pilot: **16/16** bound file digests plus self-hash passed.

All retain `provider_bytes_bundled = false` where the release contains curated published values
rather than archived provider bytes.

## Software checks

- `PYTHONPATH=src pytest -q`: **74/74 tests passed**.
- Test collection independently counted **74 tests across 20 test modules**.
- `python -m compileall -q src scripts tests`: **passed**.
- Python AST preflight: **passed for 46 Python files** under `src/`, `scripts/` and `tests/`.
- Python source line-length preflight at 100 characters: **zero violations**.
- `pyproject.toml`: parsed successfully; package version is **0.3.3**.
- Runtime `pt_he_pipeline.__version__`: **0.3.3**.
- A release-version regression test now enforces agreement between runtime package metadata and
  `pyproject.toml`.
- All five `config/*.yml` files parsed successfully as mappings.
- Study A recent-window rebuild: **passed**.
- Study A medium-run rebuild: **passed**.
- Study A demographic-sensitivity rebuild: **passed**.
- Study B matched-course rebuild: **passed**.
- DGES manifest CLI smoke test over 2003-2005: **passed**, preserving the registered transition
  from archive discovery in 2003 to the `statcol`/`statce` source family in 2004-2005.
- `ruff`: not installed in this runtime; it remains a declared CI gate.
- `mypy`: not installed in this runtime; it remains a declared CI gate.

## Paper checks

- Scientific manuscript compiled successfully with two final `pdflatex` passes.
- Paper length: **9 A4 pages**.
- PDF preflight: **9 pages, openable, unencrypted, non-scanned and without XFA**.
- The final PDF was rendered at 180 dpi and visually inspected page by page.
- The Study B table and scatter figure were inspected at full rendered-page resolution.
- No clipping, overlap, black glyph boxes or broken figures were observed.
- The LaTeX log contains no Overfull, Underfull, undefined-reference, undefined-citation or
  matched LaTeX warnings.
- A render comparison against the pre-v0.3.3 seven-page paper was generated; the new manuscript
  adds the matched-course data, methods, result and interpretation sections.

## Release boundary

Version 0.3.3 is the first narrow programme-level empirical test for Study B. It is deliberately
not a system-wide verdict. The next release should scale the same source/reconciliation contract
to a multi-course, multi-year programme-by-institution panel, validate longitudinal course and
institution concordances, and only then estimate broad demand-grade relationships. Regionality
and ranking analyses remain downstream of that measurement work.

## Release package checks

- Final repository tree contains **134 files** before archiving.
- Runtime caches, Python bytecode and LaTeX auxiliary build files are absent from the release
  tree.
- The v0.3.3 ZIP is built in sorted path order with a fixed archive timestamp.
- A fresh extraction is compared file-by-file against the release source tree using SHA-256.
- The published `.sha256` file records the final archive digest.
