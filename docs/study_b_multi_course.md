# Study B multi-course extension

## Purpose

The single-course pilot for DGES code `9119` established that the comparative `StatsCurso` tables can support an exact matched design. The next gate is to test whether that result is specific to Engineering Informatics or appears across a registered set of programmes.

This extension does **not** add rankings or regionality. It first resolves the more basic question:

> How consistently does applicants-per-vacancy account for cross-institution differences in entry grades when the programme itself is held fixed?

## Registered programme set

The first multi-course release freezes five exact DGES programme identities:

| DGES code | Programme | Degree | Domain |
|---|---|---|---|
| 9081 | Economia | Licenciatura | economics |
| 9119 | Engenharia Informática | Licenciatura | ICT |
| 9147 | Gestão | Licenciatura | management |
| 9219 | Psicologia | Licenciatura | psychology |
| 9500 | Enfermagem | Licenciatura | nursing |

The registry is based on exact code-title-degree continuity in the 2019 and 2020 DGES comparative-course publications and a deliberately heterogeneous domain selection. It is frozen before full extraction and multi-course model fitting. No course is included or excluded because its demand-grade relationship is strong or weak.

## Source and overlap design

The source family is unchanged from the pilot:

- `StatsCurso19.pdf` compares 2018 with 2019;
- `StatsCurso20.pdf` compares 2019 with 2020.

The repeated 2019 observation is a validation feature, not a nuisance duplicate. For every establishment-programme observation present in both source documents, all registered count and grade measures must agree exactly before one row is retained. A disagreement is a hard error.

## Stable-offering panel

A programme-establishment unit enters the primary stable-offering panel only if:

1. its exact programme code is observed in 2018, 2019 and 2020;
2. the 2019 observation is present in both comparative documents and reconciles;
3. the programme retains at least six such establishments.

This selection uses **source coverage only**. Demand and grades are not consulted. The rule changes the estimand from all providers in a year to providers that offer the same programme continuously across the three-year window. That restriction is reported explicitly rather than treated as innocuous.

## Zero placement and missing grades

The source layer preserves establishment-years with zero placements. A missing cut-off or mean grade is valid only when no candidate was placed. These rows remain in the stable-offering data.

The modelling panel is constructed separately and requires positive total demand and complete primary outcomes in all three years for an establishment-programme unit. Attrition from stable offering to model completeness is reported by programme. No grade is imputed.

## Primary demand measure

For establishment-programme unit \(i\) in programme \(p\) and year \(t\):

\[
D_{ipt}=\frac{A_{ipt}}{V_{ipt}},
\]

where \(A\) is total applicants and \(V\) is first-phase vacancies. Models use \(\log D_{ipt}\).

## Cross-sectional estimand

The cleanest generalisation of the original pilot is to estimate separately inside each programme-year cell:

\[
y_{ipt}=\alpha_{pt}+\beta_{pt}\log D_{ipt}+\varepsilon_{ipt}.
\]

For each primary grade outcome, the analysis reports the full distribution of programme-year \(R^2\) values rather than one pooled headline number. The registered summaries include the median, interquartile range and the proportions of cells with \(R^2\ge0.50\) and \(R^2\ge0.80\).

This makes the phrase “explains most differences” testable without requiring every programme to have the same relationship.

## Interpretation boundary

This extension remains observational. Applicants-per-vacancy is mechanically tied to selectivity because entry grades are order-statistic outcomes. Persistent institution characteristics can also affect both demand and grades.

The multi-course analysis is therefore designed to answer an explanatory and predictive question. It does not identify a causal effect of demand on grades. Rankings and regionality remain separate later layers so they cannot be used to retroactively redefine the multi-course sample.
