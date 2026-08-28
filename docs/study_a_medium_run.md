# Study A medium-run broad-area extension

## Purpose

Version 0.3.1 established the first empirical Study A layer beyond the 2023-2026
baseline without pretending that the registered 1997-2026 programme-level panel is
complete. The release uses only official first-phase broad-area tables that have been
source-locked in the repository.

The expected medium-run window is 2017-2026. Complete 23-area tables are locked for:

- 2017;
- 2018;
- 2020;
- 2021;
- 2022;
- 2023;
- 2024;
- 2025;
- 2026.

The complete broad-area table for **2019 remains unobserved**. The v0.3.2 archive audit
shows that the official standard first-phase statistics index does not list a comparable
broad-area placement table. National 2019 totals are available, but they are not enough to
reconstruct field composition. No area-level 2019 value is interpolated, inferred from
neighbouring years, or reverse-engineered from partial reports.

## Source-vintage rule

The broad-area table is not numbered identically in every vintage. The 2017 official
document calls it **Quadro XII**; the later source-locked vintages use **Quadro V**.
The validator therefore accepts only the registered table numbers and still requires
one source document per year.

Every observed year contains the same 23 canonical broad areas after spelling-only
normalisation (`Arquitectura`/`Arquitetura` and `Protecção`/`Proteção`). The source
labels themselves remain in the curated table.

## Hard reconciliation gate

For every source-locked year \(t\), the broad-area rows must satisfy:

\[
\sum_g V_{gt}=V_t,\qquad
\sum_g A^{(1)}_{gt}=A_t,\qquad
\sum_g P_{gt}=P_t,
\]

where \(V\) is vacancies, \(A^{(1)}\) first-choice candidates and \(P\)
placements. The national candidate identity holds because every valid first-phase
candidate contributes exactly one first choice.

The committed medium-run file contains 207 rows:

\[
9\text{ source-locked years}\times23\text{ areas}=207.
\]

All nine years reconcile exactly before any STEM aggregation is performed.

## Registered broad STEM mapping

The medium-run release retains the v0.3.0 crosswalk:

| Component | Published source areas |
|---|---|
| 05 — Natural sciences, mathematics and statistics | Ciências da Vida; Ciências Físicas; Matemática e Estatística |
| 06 — Information and communication technologies | Informática |
| 07 — Engineering, manufacturing and construction | Engenharia e Técnicas Afins; Indústrias Transformadoras; Arquitetura e Construção |

Both the seven source areas and the three components are released. All-STEM results
are therefore auditable back to the published categories.

## Descriptive estimands

The broad-area source supports:

\[
S_{gt}=\frac{P_{gt}}{P_{\cdot t}},\qquad
O_{gt}=\frac{P_{gt}}{V_{gt}},\qquad
F_{gt}=\frac{A^{(1)}_{gt}}{V_{gt}}.
\]

It does **not** report total programme applications by broad area. The project
therefore continues to reserve

\[
D_{gt}=\frac{A_{gt}}{V_{gt}}
\]

for the programme-level panel rather than substituting first-choice pressure.

The primary v0.3.1 medium-run descriptions are:

1. the 2017-to-2026 endpoint change in placements and placement share;
2. a log-linear placement path using calendar year as the regressor;
3. a linear placement-share gradient in percentage points per year;
4. corresponding occupancy and first-choice-pressure gradients;
5. the same fitted descriptions after the pre-specified exclusion of 2020 and 2021.

The missing 2019 source year remains a real two-year calendar gap between 2018 and
2020. It is not compressed into one pseudo-year. Year-to-year percentage change is
set to missing at 2020 for the same reason.

## Why there are no p-values in this release

These tables describe the complete published first-phase administrative counts in
the source-locked years. The fitted line is used as a compact path summary, not as a
sampling model. With only nine observed years, one missing source year and a major
pandemic-era disturbance, structural-break testing would create more apparent
precision than the data justify at this stage.

The release therefore reports slopes and descriptive \(R^2\), but no significance
claim. Causal language is not authorised.

## Medium-run result

Registered STEM placements are 13,926 in 2017 and 15,181 in 2026:

\[
\frac{15181}{13926}-1=+9.0\%.
\]

The placement share moves in the opposite direction:

\[
31.01\%\rightarrow30.37\%,
\]

or -0.64 percentage points. The components differ materially:

- group 05: -6.8% placements between the endpoints;
- group 06: +60.0%;
- group 07: +11.0%.

The all-STEM log-linear path across the nine source-locked years corresponds to
+0.46% placements per calendar year with descriptive \(R^2=0.050\). Excluding 2020
and 2021 gives +0.75% per year. The all-STEM placement-share gradient is approximately
-0.077 percentage points per year in the main description and -0.074 in the frozen
sensitivity.

The central empirical point is therefore a decomposition, not a binary verdict:
absolute STEM placements are higher at the 2026 endpoint, their share of all
placements is slightly lower, group 05 is lower, and ICT plus group 07 are higher.

## v0.3.2 demographic sensitivity

The exact age-18 denominator remains pending, but demographic scale is no longer omitted entirely. Version 0.3.2 adds a sensitivity based on the INE resident population aged 15-24 disseminated by PORDATA. The ten-year band is divided by ten to form an explicitly labelled average single-year cohort proxy; competition year `t` uses population year `t-1`.

Between the relevant population references, the 15-24 population grows by about 7.6%, while raw all-STEM placements grow by 9.0%. The corresponding cohort-proxy rate changes by only about +1.3%, from 126.4 to 128.1 placements per 1,000 average single-year cohort equivalents. Group 05 changes by -13.3%, group 06 by +48.7%, and group 07 by +3.2% on the same normalised basis.

This is a sensitivity, not a substitute for the registered exact age-18 rate. See `docs/study_a_demography.md`.

## Interpretation boundary

This medium-run layer is stronger than a four-year snapshot, but it remains
insufficient for the registered long-run proposition. It does not yet provide:

- a complete 1997-2026 programme-level panel;
- an observed 2019 broad-area field table;
- total applicants per programme/vacancy across the full period;
- the exact age-18 demographic denominator;
- validated longitudinal programme concordances through all reforms.

The result should therefore be read as **medium-run broad-area evidence**, not as the
final Study A adjudication.

## Reproduction

```bash
poetry run python scripts/build_study_a_medium_run.py
```

The build writes the medium-run result tables, figures, source-coverage table,
findings note and a self-hashed analysis receipt under `results/study_a/` and
`figures/study_a/`.
