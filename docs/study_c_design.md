# Study C design freeze — R&D talent-pipeline exposure

## Status

This document prospectively freezes the primary Study C analysis before any unit-level FCT evaluation results or institution-by-field pipeline values are inspected.

Study C asks whether high-performing Portuguese R&D units are exposed to weakening higher-education feeder pipelines. The primary result is **exposure**, not a causal effect of education-pipeline change on research performance.

## 1. Primary unit and high-performance definition

The observational unit is an FCT R&D unit from the 2023/2024 evaluation exercise, linked to explicit host institutions and scientific fields.

The primary high-performance group is:

- `Excellent`;
- `Very Good`.

Other rated units remain in the comparison universe where the public evaluation data permit. Rating categories are evaluation outcomes, not direct bibliometric measures.

The 2023/2024 rating is used to **stratify current exposure**. It is not treated as an outcome caused by the 2018–2024/25 education-pipeline trends, because the 2023/2024 evaluation itself assesses scientific activity during the overlapping 2018–2023 period.

## 2. Scientific scope

The primary feeder-field scope is the same registered STEM domain used in Study A:

- ISCED-F 05 — Natural sciences, mathematics and statistics;
- ISCED-F 06 — Information and communication technologies;
- ISCED-F 07 — Engineering, manufacturing and construction.

FCT scientific panels are cross-walked prospectively to these three domains before unit-level pipeline values are examined.

Rules:

1. one-to-one panel mappings enter the primary analysis;
2. clearly multi-domain panels receive published fractional field weights summing to one;
3. ambiguous panels are excluded from the primary analysis and may enter a pre-specified sensitivity;
4. no R&D unit is mapped to one degree course as a shortcut.

## 3. Host-institution mapping

Every eligible R&D unit receives one or more host-institution weights.

For unit `u`, institution `h`, and feeder field `f`,

\[
w_{u,h,f} \ge 0,\qquad \sum_{h,f} w_{u,h,f}=1.
\]

Primary institutional weights use public FCT organisational information in the following priority order:

1. public counts of integrated researchers or members by participating institution, when a compatible unit-level breakdown exists;
2. otherwise, equal weights across formally listed participating institutions;
3. if only one managing/host institution is publicly identifiable, weight 1 is assigned to that institution and the limitation is reported.

No weights are inferred from rankings, admissions outcomes, geographic proximity, or observed Study C results.

## 4. Feeder-pipeline components

The primary education-pipeline components come from annual higher-education administrative statistics and are reported separately:

1. first-time entrants;
2. first-cycle graduates;
3. second-cycle graduates;
4. doctoral enrolments;
5. doctoral graduates.

Research-personnel FTE from IPCTN is **not** part of the feeder composite. It is an end-stage research-stock/context variable and is reported separately.

No stage is silently substituted for another when coverage is missing.

## 5. Time windows

### 5.1 Education pipeline

Primary exposure window: academic years 2018/19 through 2024/25, restricted to years with complete and comparable public RAIDES coverage for the relevant institution × field cell.

For each component `k`, institution `h`, field `f`, and year `t`, let `X_{khft}` denote the observed count.

A component trend is estimated only when at least five comparable annual observations are available.

### 5.2 Research personnel

IPCTN research-personnel FTE is reported over calendar years 2018–2024 where institution × field comparability is available.

### 5.3 FCT evaluation timing

The 2023/2024 FCT evaluation is contemporaneous with much of the 2018–2023 scientific-activity period. Therefore:

- 2023/2024 rating is a **stratifier**, not a downstream outcome of the primary pipeline window;
- any future rating or research outcome occurring strictly after the frozen exposure window may be analysed later as a secondary lagged outcome;
- no causal or predictive downstream-outcome model is run in this phase.

## 6. Component-level exposure metrics

For a positive component series with sufficient coverage, the primary trend summary is the log-linear annual path:

\[
\log X_{khft}=\alpha_{khf}+\beta_{khf}t+\varepsilon_{khft}.
\]

Report:

\[
g_{khf}=100\{\exp(\widehat\beta_{khf})-1\}.
\]

When zeros occur, the primary result reports endpoint and linear-count sensitivity rather than adding an arbitrary offset inside the logarithm.

For R&D unit `u`, the weighted component exposure is:

\[
G_{uk}=\sum_{h,f} w_{u,h,f}g_{khf}.
\]

Negative `G_{uk}` means the weighted feeder component is weakening over the registered window; positive values mean strengthening.

## 7. Primary Study C estimands

The primary outputs are descriptive exposure summaries, not hypothesis-test coefficients.

### C1. Unit-level component exposure

For every eligible unit, report the vector

\[
\mathbf G_u=(G_{u,entrants},G_{u,cycle1},G_{u,cycle2},G_{u,doctoral\ enrolment},G_{u,doctoral\ graduates}).
\]

### C2. Exposure distribution by FCT rating

Compare the distributions of each `G_{uk}` across:

- Excellent/Very Good units;
- all other eligible rated units.

Primary summaries are median, interquartile range, and empirical distribution plots. These are descriptive comparisons only.

### C3. High-performing-unit vulnerability count

For each high-performing unit, count the number of feeder components with negative weighted trends among components with sufficient coverage.

Report the full count distribution and the underlying components. No universal vulnerability threshold is used in the primary result.

### C4. Contextual research-personnel path

Report weighted 2018–2024 research-personnel FTE trends separately. These are not folded into the feeder-vulnerability count.

## 8. Exploratory composite

A composite score is secondary and may be computed only after component-level results are frozen.

If used, each component trend is standardised across eligible units and combined with equal weights over available feeder components:

\[
C_u=-\frac{1}{K_u}\sum_{k\in\mathcal K_u} z(G_{uk}).
\]

Higher `C_u` means weaker relative pipeline exposure.

Sensitivity analyses must report leave-one-component-out composites. The paper may not present the composite without the component vector.

## 9. Missingness and support

- Missing values remain missing; zero is used only for documented structural zeros.
- A unit-level component is unsupported when any required institution × field cell lacks the minimum time coverage and no prospectively valid aggregation is available.
- The unit-level denominator `K_u` is reported for every composite or vulnerability count.
- Results are reported with coverage counts before any rating-group comparison.
- No institution or field is imputed from a ranking, neighbouring field, or national average.

## 10. Interpretation boundary

The primary permissible conclusion is of the form:

> Some currently high-performing R&D units are more or less exposed to weakening feeder-pipeline components under the registered institution × field mapping.

The primary analysis cannot establish that:

- falling entrants cause future research decline;
- FCT ratings are caused by feeder-pipeline conditions;
- high-performing units will necessarily face staffing problems;
- one pipeline stage can stand in for the complete research-career pathway.

International recruitment, migration, field switching, labour-market competition, funding, researcher mobility, and institutional hiring all intervene between higher-education cohorts and R&D capacity.

## 11. Secondary downstream-outcome gate

A later outcome analysis is permitted only if a research outcome is observed strictly after the registered exposure window and a defensible lag is available.

Eligible future outcomes may include:

- integrated researcher counts;
- research-personnel FTE;
- unit funding;
- a later FCT evaluation wave.

Any such analysis requires a separate prospective design freeze. The present Study C phase stops at exposure and contemporaneous descriptive context.

## 12. Reproducibility contract

Before unit-level values are inspected, the implementation must commit:

1. FCT-unit registry and rating-source manifest;
2. FCT-panel-to-ISCED field crosswalk;
3. R&D-unit-to-institution weight table;
4. RAIDES source manifest and exact variable definitions;
5. IPCTN source manifest and exact FTE definition;
6. coverage audit by year, institution, field and component;
7. tests enforcing weights summing to one, no unregistered fields, no post-hoc imputation, and minimum time support.

Only after those artefacts are merged may the first unit-level exposure results be generated.
