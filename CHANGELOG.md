# Changelog

## 0.3.4 — 2026-09-07

- Close the current Study A empirical phase on the source-locked 2017, 2018 and 2020-2026 first-phase broad-area panel, preserving 2019 as an unobserved field-composition year rather than imputing it.
- Promote the source-locked INE population aged exactly 18 to the preferred demographic denominator; retain the 15-24 divided-by-ten proxy only as a weaker secondary sensitivity.
- Consolidate the headline Study A result: all-STEM placements are +9.0% between 2017 and 2026, the exact age-18-normalised endpoint rate is +9.1%, and placement share is -0.64 percentage points.
- Preserve component heterogeneity: group 05 declines over the endpoints, while groups 06 and 07 increase materially.
- Record that the available 2017-2026 evidence does not support describing absolute first-phase STEM placements as one sustained decline.
- Keep the five-programme Study B work as secondary cross-domain calibration rather than primary STEM evidence.
- Freeze programme-classification and continuity machinery for optional future historical extension without making the 1997-2026 programme reconstruction a blocker for the current release.
- Move historical programme-level reconstruction and further Study B scaling to future work.
- Treat Study C as a separate downstream R&D-pipeline research track rather than a prerequisite for closing the current admissions/STEM phase.
- Enter consolidation freeze: no further parser, sensitivity, concordance or source-ingestion work for this phase unless it fixes a demonstrated defect, incorporates materially new official evidence, or is required for publication/reproducibility packaging.

## 0.3.3 — 2026-08-26

- Add the first programme-level matched-course pilot using DGES course code 9119, `Engenharia Informática [Licenciatura]`, across 23 institutions in 2018-2020.
- Transcribe two consecutive official `StatsCurso` comparative publications into a 92-row source layer and preserve the 23 duplicated 2019 institution-course observations.
- Require exact equality of all duplicated 2019 vacancies, applicant counts, placements and grade measures before building the 69-row canonical panel.
- Recover total applicants per vacancy, first-choice pressure, placement occupancy, general-contingent cut-off and mean application grade for the exact matched course.
- Add year-specific log-demand associations, nested year/institution/demand descriptions and leave-one-year-out prediction without causal or sampling-inference claims.
- Show that applicants per vacancy account for 55.9%-74.3% of cut-off variation and 49.8%-76.6% of mean placed-grade variation across institutions within individual years of this pilot.
- Show that institution structure absorbs much persistent between-institution variation while demand still improves leave-one-year-out prediction.
- Add source manifests, typed validation/modelling code, release-data contracts, figures, result receipts and paper integration.
- Keep rankings, regionality and generalisation beyond course 9119 explicitly deferred.

## 0.3.2 — 2026-08-25

- Audit the official DGES 2019 first-phase archive and record that its standard index does not list a comparable complete broad-area placement table; preserve the 2019 field-composition gap without imputation.
- Add a source-registered INE/PORDATA resident-population series for ages 15-24 covering 2016-2025.
- Add a typed demographic-sensitivity module using the preceding-year 15-24 population divided by ten as an explicitly labelled average single-year cohort proxy; never relabel it as population aged 18.
- Add all-STEM and component-level cohort-proxy metrics, endpoint comparisons, a raw-versus-normalised figure, findings note and self-hashed analysis receipt.
- Show that the 2017-2026 all-STEM endpoint change moves from +9.0% in raw placements to +1.3% on the broad-cohort proxy; group 05 is -13.3%, group 06 +48.7%, and group 07 +3.2% on the same normalised basis.
- Keep raw counts and placement share as co-primary outcomes and retain the exact age-18 denominator as an unresolved registered input.
- Update the scientific paper to distinguish raw growth, relative placement share and demographic-scale normalisation explicitly.
- Expand the test suite with demographic-policy, denominator-coverage and release-data contracts.

## 0.3.1 — 2026-08-25

- Extend Study A to a source-locked 2017-2026 broad-area window with nine observed years and an explicit 2019 source gap.
- Add official complete broad-area transcriptions for 2017, 2018, 2020, 2021 and 2022; retain and revalidate the 2023-2026 layer.
- Register the 2017 `Quadro XII` vintage explicitly rather than assuming that every year uses `Quadro V`.
- Add a 207-row medium-run area panel and require exact annual reconciliation to national vacancies, valid candidates and placements before STEM aggregation.
- Prevent non-consecutive observations from being labelled year-on-year changes: 2020 `placement_yoy_change` is missing because 2019 is not observed.
- Add typed descriptive trend machinery using actual calendar-year spacing, with log-placement trends, placement-share gradients, occupancy and first-choice-pressure paths.
- Freeze a sensitivity that excludes 2020 and 2021; do not report sampling p-values or structural-break claims from the nine-year administrative series.
- Add source-coverage output, medium-run component/source-area/aggregate results, endpoint comparisons, three figures, a findings note and a self-hashed analysis receipt.
- Update the paper and claim registry with the medium-run result: all-STEM placements are +9.0% from 2017 to 2026, while placement share is -0.64 percentage points and component paths diverge.
- Keep the registered 1997-2026 programme-level Study A open; no 2019 field values, programme applications or demographic denominators are fabricated.

## 0.3.0 — 2026-08-25

- Add the first empirical Study A baseline using official DGES first-phase Quadro V broad-area tables for 2023-2026.
- Preserve all 23 published areas and hard-reconcile annual vacancies, first-choice candidates and placements to official national totals before analysis.
- Add a deterministic broad-area crosswalk for registered STEM groups 05, 06 and 07 while retaining the seven underlying source areas.
- Add typed validation and aggregation functions plus committed release-data tests.
- Add receipt-bound result tables for source areas, STEM components, the all-STEM annual series and endpoint comparisons.
- Add reproducible figures for aggregate placements, component placement indices and placement share.
- Record the provenance boundary explicitly: the recent public tables are curated transcriptions with source registration and content hashes, not falsely labelled raw-provider receipts.
- Add the first empirical paper-results section and expand the paper from 3 to 5 pages.
- Document the v0.3 result as recent-window, heterogeneous and non-monotonic; the long-run 1997-2026 proposition remains unadjudicated.
- Correct the documented `cna_pairs` and mobility data contracts to match the v0.2 implementation.

## 0.1.0 — 2026-08-25

- Freeze three empirical propositions covering STEM placements, regionality/demand/entry grades, and the R&D talent pipeline.
- Add a source registry centred on DGES, DGEEC, FCT and INE.
- Add typed metrics, validation, DGES document discovery and content-addressed download receipts.
- Add tests, CI, reproducibility notes and a LaTeX paper scaffold.
