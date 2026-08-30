# Study B regionality design

## Question

This layer studies how strongly Portuguese higher-education preferences and realised
placements are geographically concentrated. It does not assume that regionality is
strong or weak in advance.

The primary contrast separates two outcomes published by DGES:

1. **first choice** — the cleaner observed preference outcome;
2. **placement** — the realised allocation after grades, capacity and competition bind.

The two should not be conflated.

## Source design

The primary registered window is 2023-2025. The 2024 and 2025 DGES comparative
`Mobilidade` publications each contain two consecutive competition years, creating an
independent overlap in 2024. Every duplicated 2024 origin-destination cell must agree
exactly across the two publications before canonicalisation.

The source contract preserves the published geography on both axes. Recent mobility
tables contain the 18 mainland districts plus the two autonomous regions as destination
areas. Historical source vintages can also contain legacy access areas. Districts,
autonomous regions and access areas therefore use explicit area-type fields and are not
silently relabelled.

## Primary estimands

For flow type \(f\) and year \(t\), let \(C_{oatf}\) be the published flow from origin
area \(o\) to destination area \(a\).

The first reported quantity is comparable-origin coverage:

\[
K_{tf} =
\frac{\sum_{o \in D}\sum_a C_{oatf}}
     {\sum_o\sum_a C_{oatf}},
\]

where \(D\) is the set of origins explicitly published as districts.

Conditional on that comparable-origin subset, the same-district share is

\[
R_{tf} =
\frac{\sum_{d \in D} C_{ddtf}}
     {\sum_{o \in D}\sum_a C_{oatf}}.
\]

The numerator uses only district-to-same-district cells. Flows from a district to an
autonomous region remain in the denominator because they are genuine observed mobility,
but they are not reclassified onto a district diagonal.

`R` is never reported without `K`. A high diagonal share based on a small comparable
subset would otherwise be misleading.

The primary within-year contrast is

\[
\Delta_t = R_{t,\mathrm{placement}} - R_{t,\mathrm{first\ choice}}.
\]

A positive value means realised placements are more same-district concentrated than
first choices; a negative value means they are less concentrated. This contrast remains
descriptive and is not interpreted causally.

## Secondary structure measures

The design also registers conditional destination entropy and normalised mutual
information. These prevent the analysis from relying only on the diagonal. A country
can have the same diagonal share under very different off-diagonal mobility structures.

## Interpretation boundary

This layer does not include rankings. It also does not pool the already-estimated
applicants-per-vacancy relationship into the geography model. Those are distinct parts
of Study B and are joined only after each has its own validated evidence layer.

The analysis uses complete administrative flow tables rather than a probability sample.
Sampling p-values are therefore not the primary inferential object. Uncertainty arising
from measurement, source comparability and alternative geographic definitions is handled
through explicit sensitivity analyses instead.
