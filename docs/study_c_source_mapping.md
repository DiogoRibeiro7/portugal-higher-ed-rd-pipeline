# Study C source and mapping gate

This gate is prospective. It resolves source provenance and mapping rules before any unit-level exposure metric is calculated.

## Canonical FCT registry dependency

The 2023/2024 FCT R&D-unit evaluation call page is the canonical public entry point. The final-results document is linked through a myFCT document endpoint. In the current execution environment the call page can be verified but the linked final-results payload cannot be retrieved reproducibly. Therefore the canonical unit registry is explicitly marked as an author-supplied/manual-download dependency.

No search-engine snippet, university news item, unit website or institutional press release may substitute for the canonical final-results table when establishing the complete unit universe or final rating distribution.

Before unit-level Study C analysis can run, the author-supplied FCT file must be stored outside tracked source data, hashed, and validated against a committed contract containing at minimum unit identifier, unit name, scientific panel, final rating and formal participating/host institution information available in the source.

## Panel to feeder-field mapping

The primary Study C feeder scope is ISCED-F 05, 06 and 07. FCT scientific panels are mapped to those broad feeder fields prospectively in `data/curated/fct/study_c_panel_isced_crosswalk.csv`.

The mapping is deliberately broad. It is not a claim that every student in one ISCED field is a potential recruit to every unit in the corresponding FCT panel. It defines the eligible feeder-field universe for later institution-weighted exposure calculations.

Units whose FCT panel lies outside 05/06/07 are outside the primary Study C population. Interdisciplinary or multi-panel units require an explicit documented rule from the canonical FCT source; no panel is inferred from unit names.

## Institution identity contract

All source-specific institution labels are mapped to a stable canonical institution identifier before joining. The mapping table must contain:

- `source_system`;
- `source_institution_id` where supplied;
- `source_institution_name`;
- `canonical_institution_id`;
- `canonical_institution_name`;
- `valid_from` and `valid_to` when a merger or rename matters;
- `mapping_basis`;
- `source_reference`.

Name-only fuzzy matching is forbidden in production. Normalised names may be used to generate candidates for manual review, but the committed concordance must contain the explicit accepted mapping.

## Unit to institution weights

Weights are data, not model outputs. For each unit `u`, institution `h` and feeder field `f`, the final table must satisfy

\[
\sum_{h,f} w_{u,h,f}=1.
\]

The frozen evidence priority is:

1. public member/integrated-researcher counts by institution where the official or unit source provides them;
2. equal weights across formally listed participating institutions when counts are unavailable;
3. weight one on the sole formally identified host/manager when the unit is single-institution.

The table must record `weight_basis`, `source_reference` and whether the weight is count-derived or equal-share. Rankings, admissions outcomes, geographic proximity and Study C pipeline results may never influence these weights.

## RAIDES variable contract

The education-pipeline series are institution × feeder-field × academic-year counts. The primary window is 2018/19–2024/25. Required components are kept separate:

- first-time entrants;
- first-cycle graduates;
- second-cycle graduates;
- doctoral enrolments;
- doctoral graduates.

A component enters a trend calculation only with at least five comparable annual observations. Missing observations are never replaced by zero. Structural zeros are retained as zeros but are not given arbitrary log offsets.

## IPCTN variable contract

Research-personnel FTE for 2018–2024 is contextual. It is not an upstream feeder component and is excluded from any feeder composite or weakening-component count.

## Coverage audit before results

The first executable Study C audit must report, without exposure estimates:

- number of canonical FCT units recovered;
- number and share in the primary 05/06/07 scope;
- rating completeness;
- institution-mapping completeness;
- weight-table completeness and sum-to-one checks;
- RAIDES support counts by institution × field × component;
- IPCTN contextual coverage.

If a required source cannot support institution × field resolution, the corresponding component remains unavailable. The pipeline must not manufacture detail by allocating national or sector totals to institutions.
