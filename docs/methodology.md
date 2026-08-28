# Methodology

## 1. Study A — STEM access and placement

### 1.1 Population and period

The preferred dataset is the complete first-phase CNA institution/course panel for every recoverable year from 1997 to 2026. If variable definitions or file layouts break comparability, the common period is shortened rather than silently spliced.

### 1.2 Field classification

Programmes are cross-walked to ISCED-F 2013. The primary STEM definition comprises:

- 05 — Natural sciences, mathematics and statistics;
- 06 — Information and communication technologies;
- 07 — Engineering, manufacturing and construction.

Every aggregate result is accompanied by the three components. This prevents growth in ICT from masking decline in natural sciences, or vice versa.

### 1.3 Outcomes

For course–institution pair \(i\) in year \(t\):

\[
D_{it}=\frac{A_{it}}{V_{it}},\qquad
F_{it}=\frac{A^{(1)}_{it}}{V_{it}},\qquad
O_{it}=\frac{P_{it}}{V_{it}},
\]

where \(A\) is applicants, \(A^{(1)}\) first-choice applicants, \(V\) vacancies and \(P\) placements.

At field-year level we report counts, shares and rates per 1,000 people of the relevant age. The demographic denominator is a sensitivity choice and is never used to erase the raw series.

### 1.4 Trend analysis

Primary trend summaries use log-count and share regressions with year effects reported graphically. Non-linear smooths and break-point procedures are exploratory because selecting breaks from the same series can overstate certainty.

The COVID-affected admission years are retained in the main series and excluded in a pre-specified sensitivity check.

### 1.5 Recent-window baseline

Before the full historical panel is available, v0.3 reports a deliberately narrow
2023-2026 baseline from DGES first-phase Quadro V broad-area tables. All 23 source
areas are retained and reconciled to the national totals before the seven STEM
source areas are aggregated into registered groups 05, 06 and 07.

The compact table supports occupancy, first-choice pressure and placement share,
but not total applicants per vacancy by area. First-choice candidates are therefore
not substituted for total applicants. No log-linear trend, break-point estimate or
demographic-normalised rate from this four-year baseline is promoted to the
long-run result. Endpoint changes and year-to-year movements are descriptive only.

See `docs/study_a_recent.md` for the exact crosswalk and validation identities.

### 1.6 Medium-run broad-area extension

Version 0.3.1 extends that publication-table layer to the source-locked years 2017,
2018 and 2020-2026. The expected 2017-2026 window contains an explicit 2019 source
gap. No field value is imputed. The 2017 source uses `Quadro XII`; later locked
vintages use `Quadro V`. All observed years contain 23 comparable canonical source
areas and must reconcile exactly to national vacancies, valid candidates and
placements.

The medium-run fitted descriptions use actual calendar year as the regressor. The
2018-to-2020 gap therefore spans two units, and the 2020 `placement_yoy_change` value
is deliberately missing rather than presented as a one-year change. The main
log-count path and share gradient use all source-locked years; a frozen sensitivity
excludes 2020 and 2021.

No sampling p-values or formal break claims are reported for this layer. The records
are administrative population counts, and nine observed years with one source gap
are too thin for a credible data-driven break search. The fitted slope and \(R^2\)
are descriptive effect-size summaries only. See `docs/study_a_medium_run.md`.

Version 0.3.2 adds a demographic sensitivity using the preceding-year INE/PORDATA
population aged 15-24 divided by ten. This is an average single-year cohort proxy, not
the registered exact age-18 denominator. Raw counts and placement shares remain
co-primary, and the proxy is reported only to assess demographic scale sensitivity.

## 2. Study B — regionality, demand and grades

### 2.1 Regionality

Let \(F_{odt}\) be the number of applicants from origin district \(o\) whose first preference lies in destination district \(d\) at year \(t\).

The simplest statistic is the same-district share:

\[
R_t=\frac{\sum_d F_{ddt}}{\sum_o\sum_d F_{odt}}.
\]

This is complemented by normalised entropy, mutual information and origin-specific destination shares. A high diagonal share supports regional concentration, but the magnitude is reported rather than converted to an arbitrary “regional/not regional” label.

A gravity-style extension can model flows as a function of geographic distance, destination capacity, field availability and institution characteristics.

### 2.2 Demand and entry grades

The course–institution–year panel is analysed with nested specifications. A representative sequence is:

\[
y_{ijt}=\alpha+\mu_i+\lambda_t+\varepsilon_{ijt},
\]

\[
y_{ijt}=\alpha+\mu_i+\lambda_t+f(D_{ijt})+\varepsilon_{ijt},
\]

\[
y_{ijt}=\alpha+\mu_i+\lambda_t+\eta_j+f(D_{ijt})+\varepsilon_{ijt},
\]

where \(y\) is an entry-grade outcome, \(i\) a comparable course/field, \(j\) an institution and \(D\) demand pressure.

The project reports:

- adjusted \(R^2\) and incremental \(R^2\);
- partial sums of squares where meaningful;
- leave-one-year-out RMSE and MAE;
- residual institution effects;
- weighted and unweighted versions.

The applicants/vacancy ratio has a structural relation with cut-off grades: more applicants competing for a fixed number of places changes the selected order statistic. A large coefficient is therefore not automatically evidence of a behavioural causal mechanism.

#### 2.2.1 Matched-course pilot

Version 0.3.3 implements the first programme-level design on DGES course code 9119,
`Engenharia Informática [Licenciatura]`, for 2018-2020. The same 23 institutions are
observed in every year. The 2019 and 2020 comparative-course publications both report
2019, creating 23 duplicated institution-year records. All counts and grade measures
must agree exactly across those two sources before one canonical 2019 row is retained.

For institution \(j\) and year \(t\), the primary pilot predictor is

\[
D_{jt}=\frac{A_{jt}}{V_{jt}},
\]

with \(A\) total applicants and \(V\) initial vacancies. First-choice pressure is
analysed separately. The descriptive cross-sectional model within each year is

\[
y_{jt}=\alpha_t+\beta_t\log D_{jt}+e_{jt}.
\]

The nested pooled descriptions compare a linear calendar-year term, year plus demand,
institution fixed effects plus year, and institution fixed effects plus year and demand.
The same specifications are evaluated by holding out each complete year. The time term
is linear in calendar year so a held-out year can be predicted; institution levels are
fixed because all 23 institutions appear in all three years.

No sampling p-values are used to turn this administrative-data pilot into an inferential
claim. The reported quantities are coefficients, \(R^2\), incremental \(R^2\), RMSE
and MAE. Generalisation beyond course 9119 is prohibited at this stage.

### 2.3 Rankings

Historical rankings are an optional layer because data access and methodology change across providers. When supplied, each observation must include provider, publication date, rank/rank band, score where available and a provenance reference.

Ranking variables enter *after* the core geography/demand models. The result of interest is the change in out-of-sample error and explanatory power. If institution fixed effects absorb nearly all time-invariant reputation, a cross-sectional ranking coefficient is not interpreted as a within-institution effect.

## 3. Study C — R&D pipeline exposure

### 3.1 Unit definition

The primary high-performance group is FCT units rated *Excellent* or *Very Good*. Analyses are also stratified by scientific domain and unit size.

### 3.2 Pipeline components

For each host-institution × feeder-field series, the project tracks:

1. first-time entrants;
2. first-cycle graduates;
3. second-cycle graduates;
4. doctoral enrolments;
5. doctoral graduates;
6. research personnel (FTE where available).

Because these stages occur at different lags, the project estimates cohort-consistent windows where data permit. It does not compare an entrant count in year \(t\) directly with doctoral output in the same year as though they were the same cohort.

### 3.3 Exposure mapping

Each R&D unit receives weights over host institutions and feeder fields:

\[
\sum_{h,f} w_{u,h,f}=1.
\]

Primary results show the underlying components. An exploratory pipeline pressure score can be constructed from standardised growth measures only after its weights are published and sensitivity-tested.

### 3.4 Downstream outcomes

Where the historical data are sufficiently deep, lagged pipeline exposure is related to subsequent:

- integrated researcher counts;
- research personnel FTE;
- unit funding;
- FCT evaluation changes.

The small number of FCT evaluation waves sharply limits causal inference. If future outcomes have not yet occurred, the analysis stops at measured exposure.

## 4. Missing data and comparability

- Missing values are never silently converted to zero.
- Structural zeros (for example, zero placements with positive vacancies) are encoded separately from missing reports.
- Institution mergers, course renamings and degree reform are recorded in a concordance table.
- Bologna-era programme changes are treated as a comparability issue, not merely a new label.
- Changes to the CNA access rules are recorded as policy metadata.

## 5. Multiplicity and interpretation

The three studies answer related but distinct questions. The project emphasises effect sizes and uncertainty rather than a binary omnibus verdict. Where many fields or institutions are compared, false-discovery-rate adjusted results are supplied as a secondary diagnostic.
