# Roadmap

## v0.1 — research design and reproducibility scaffold — complete

- freeze the three propositions;
- define data contracts and source registries;
- establish typed package, tests, CI and LaTeX paper.

## v0.2 — deterministic DGES source architecture — complete

- model historical DGES source vintages explicitly;
- separate pair-statistics and placement/cut-off source families;
- add content-addressed raw-data receipts and reconciliation gates;
- preserve historical mobility geography and conservative concordances.

## v0.3.0 — recent Study A empirical baseline — complete

- curate and reconcile complete 2023-2026 first-phase broad-area tables;
- publish registered STEM source-area, component and aggregate metrics;
- document the 2025 trough and 2026 rebound without extrapolating four years into a long-run claim.

## v0.3.1 — medium-run Study A broad-area extension — complete

- source-lock complete broad-area tables for 2017, 2018 and 2020-2026;
- preserve 2019 as an explicit unobserved source year;
- reconcile all nine observed years to national controls;
- add calendar-time descriptive trend summaries and a frozen 2020-2021 exclusion sensitivity;
- update the empirical paper and result receipt.

## v0.3.2 — demographic sensitivity and 2019 archive audit — complete

- audit the official 2019 first-phase archive and make the absence of a comparable broad-area table explicit;
- add the INE/PORDATA 15-24 population series as a source-registered demographic input;
- construct a preceding-year average single-year cohort proxy without presenting it as exact age-18 population;
- publish raw-versus-cohort-proxy endpoint comparisons for registered STEM components;
- source-lock the exact INE age-18 denominator and promote it to the preferred demographic normalisation.

## v0.3.3 — matched-course programme-level pilot — complete

- source-lock official 2018-2019 and 2019-2020 DGES comparative-course values for course 9119;
- preserve 92 source rows and use the 23 duplicated 2019 records as an exact cross-vintage reconciliation gate;
- build a balanced 69-row panel for 23 institutions across 2018-2020;
- recover total applicants, first-choice applicants, vacancies, placements and grade outcomes;
- estimate year-specific demand/grade associations, nested institution/demand descriptions and leave-one-year-out prediction;
- prohibit generalisation beyond the matched course and defer rankings and regionality.

## v0.3.4 — Study A consolidation — complete

- retain the source-locked 2017, 2018 and 2020-2026 broad-area first-phase panel as the current empirical Study A window;
- retain the exact source-locked age-18 denominator as the preferred demographic normalisation;
- preserve the 2019 field-composition gap without interpolation or reconstruction;
- report groups 05, 06 and 07 separately before all-STEM aggregation;
- conclude that the available 2017-2026 evidence does not support a sustained decline in absolute first-phase STEM placements: the endpoint count is +9.0%, the exact age-18-normalised endpoint rate is +9.1%, and the placement share is -0.64 percentage points;
- preserve the materially different component paths: group 05 decreases, while groups 06 and 07 increase over the endpoints;
- retain the five-programme Study B work as secondary cross-domain calibration rather than primary STEM evidence;
- freeze programme-classification and continuity machinery for future historical extensions without making the 1997-2026 reconstruction a blocker for the current release;
- enter consolidation freeze for the current admissions/STEM phase.

## Current release boundary

The current empirical Study A phase is complete for the source-locked 2017-2026 window. The repository should not add further admission-source, parser, concordance or sensitivity slices merely to increase historical depth.

The historical 1997-2026 programme-level reconstruction is now **future work**, not a release gate. It should be reopened only if recoverable historical programme-level sources and defensible identity/classification concordances materially extend the estimand. The existing concordance code and DGEEC classification tooling are retained for that purpose.

Further Study B scaling is optional secondary work. The existing matched-course and five-programme evidence is not promoted into the headline STEM claim.

## Future work — not blockers for the current Study A release

### Historical Study A extension

- source-lock additional historical programme-level CNA vintages where recoverable;
- validate programme-to-ISCED-F concordances through renamings, mergers and Bologna-era reforms;
- shorten the historical primary period rather than silently splice incomparable programme regimes;
- execute a 1997-2026 or shorter programme-level analysis only if its prospective coverage gate becomes satisfiable.

### Study B extension

- extend regionality and programme-level demand/grade evidence only when a new substantive question warrants it;
- add ranking information only as a separately identified predictive layer;
- do not treat further cross-domain Study B coverage as necessary to finish Study A.

### Study C — separate downstream research track

- harmonise RAIDES / graduate / doctoral / R&D personnel series;
- construct unit-host-field exposure weights;
- link to FCT evaluation vintages and unit characteristics;
- distinguish current pipeline exposure from realised downstream outcomes.

Study C is a distinct downstream research question and is not required to close the current admissions/STEM empirical phase.

## Consolidation rule

No new theorem, model, sensitivity, parser or source-ingestion PR should be opened for the current phase unless it fixes a demonstrated defect, incorporates materially new official evidence, or is required for publication/reproducibility packaging.
