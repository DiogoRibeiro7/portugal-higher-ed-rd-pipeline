# Study B matched-course demand/selectivity pilot

## Purpose

Version 0.3.3 is the first programme-level implementation of Study B. It is deliberately
narrow: the course is held fixed at DGES code **9119 — Engenharia Informática
[Licenciatura]**, and the same 23 institutions are followed in 2018, 2019 and 2020.
The pilot tests the source contract, reconciliation logic and statistical decomposition
before any claim is generalised to all programmes.

It addresses only Proposition 2B: demand pressure and entry grades. Regionality and
rankings remain separate pending analyses.

## Official sources

Two DGES first-phase comparative course-statistics publications are used:

- 2018-2019: `https://www.dges.gov.pt/guias/pdfs/statcol/2019/StatsCurso19.pdf`;
- 2019-2020: `https://www.dges.gov.pt/guias/pdfs/statcol/2020/StatsCurso20.pdf`.

For each institution-course pair the tables report initial vacancies, total applicants,
first-choice applicants, total placements, first-choice placements, the last-placed
general-contingent grade and mean grade components.

Provider PDF bytes are not bundled in this release. The committed source table is a
curated transcription from the official publications and is labelled accordingly.

## Cross-vintage overlap as a validation gate

The 2019 observations appear in both publications. The source layer therefore contains

\[
23\times 2 + 23\times 2 = 92
\]

publication-document observations rather than prematurely deduplicating 2019.

For each institution, define the registered measure vector

\[
Z_{jt}=(V,A,A^{(1)},P,P^{(1)},c,\bar g,\overline{PI},\overline{12}).
\]

The canonical 2019 observation is eligible only if

\[
Z^{(2019\ document)}_{j,2019}
=
Z^{(2020\ document)}_{j,2019}
\]

component by component. All 23 institutions pass this equality check. The canonical
panel then contains

\[
23\times3=69
\]

institution-year rows.

## Variables

The primary demand pressure is

\[
D_{jt}=\frac{A_{jt}}{V_{jt}},
\]

where \(A\) is total applicants and \(V\) initial first-phase vacancies. A secondary
pressure measure is

\[
F_{jt}=\frac{A^{(1)}_{jt}}{V_{jt}}.
\]

The two primary outcomes are:

1. the last-placed general-contingent grade;
2. the mean application grade of placed candidates.

Grades are on the DGES 0-200 scale. Placements can exceed initial vacancies when
additional tied places are created, so occupancy above one is permitted and is not
treated as a validation failure.

## Descriptive cross-sections

Within each year the pilot fits

\[
y_{jt}=\alpha_t+\beta_t\log D_{jt}+e_{jt}.
\]

With applicants per vacancy, the observed \(R^2\) values are:

| Year | Cut-off grade | Mean placed grade |
|---:|---:|---:|
| 2018 | 0.647 | 0.498 |
| 2019 | 0.559 | 0.620 |
| 2020 | 0.743 | 0.766 |

The relationship is strong for this matched course, but it does not constitute a
near-complete explanation in every year.

## Nested descriptions

Four specifications are compared for each outcome:

\[
\begin{aligned}
M_0 &: y_{jt}=\alpha+\tau(t-2019)+e_{jt},\\
M_1 &: M_0+\beta\log D_{jt},\\
M_2 &: M_0+\eta_j,\\
M_3 &: M_2+\beta\log D_{jt}.
\end{aligned}
\]

For the cut-off grade, \(R^2\) moves from 0.058 in \(M_0\) to 0.674 in \(M_1\), and
from 0.953 in \(M_2\) to 0.973 in \(M_3\). For the mean placed grade, the corresponding
values are 0.105, 0.679, 0.958 and 0.976.

The incremental contribution of demand is therefore large relative to a year-only
baseline, but much smaller after persistent institution structure is absorbed:

\[
\Delta R^2_{M_1-M_0}=0.616\quad\text{and}\quad
\Delta R^2_{M_3-M_2}=0.020
\]

for the cut-off, and 0.574 and 0.018 for the mean placed grade.

These facts are complementary rather than contradictory. Institutions with persistently
high demand also have persistently high grades, so institution fixed effects absorb a
large part of the same between-institution structure.

## Leave-one-year-out prediction

Each complete year is held out in turn. A linear calendar-year term is used so the
held-out year can be predicted, and the institution set is fixed because all 23
institutions appear every year.

Mean held-out RMSE across the three folds is:

| Outcome | Institution + year | + demand |
|---|---:|---:|
| Cut-off grade | 9.10 | 7.49 |
| Mean placed grade | 6.51 | 5.13 |

Demand therefore adds out-of-year predictive information even after persistent
institution differences are included.

## Interpretation

This pilot establishes three points only:

- the DGES comparative-course source family can recover the variables needed for the
  registered demand/selectivity analysis;
- applicants per vacancy contain substantial information about grade differences when
  the exact course is held fixed;
- persistent institution structure also explains a large share of the observed
  differences, so a one-variable narrative is incomplete.

It does **not** identify a causal demand effect, test rankings, measure regionality, or
support generalisation to all Portuguese programmes. The next evidence gate is to apply
the same contract to a broad and historically comparable set of programmes.
