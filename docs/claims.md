# Claim registry

The project begins from three propositions raised in public discussion. They are recorded here in neutral, testable form. The repository does not encode a preferred result.

## Proposition 1 — declining placements in science and engineering

**Public proposition:** placements in science and engineering continue to fall.

### Testable form

Determine whether, over the available first-phase CNA history, the following series show sustained decline:

- absolute placements;
- share of all placements;
- applicants;
- first-choice applicants;
- applicants per vacancy;
- occupancy rate;
- age-normalised placement rate.

### Important distinctions

A decline in placements is not by itself evidence of lower student preference. Placements depend on applicant numbers, the number of places offered, eligibility and the allocation mechanism. The analysis therefore decomposes demand, supply and realised placement.

### v0.3.2 medium-run evidence status

The source-locked broad-area layer now covers 2017, 2018 and 2020-2026. The official 2019 standard archive has been audited and does not list the comparable complete
broad-area table; the missing field observation is not imputed. Across the observed
endpoints, registered STEM placements rise from 13,926 in 2017 to 15,181 in 2026
(+9.0%), while their share of all first-phase placements falls from 31.01% to 30.37%
(-0.64 percentage points).

The aggregate again hides different field paths. Between 2017 and 2026, group 05 is
6.8% lower, group 06 is 60.0% higher, and group 07 is 11.0% higher. A descriptive
all-STEM log-linear fit across the nine source-locked years corresponds to +0.46% per
calendar year (R² = 0.050); excluding 2020-2021 gives +0.75%.

This evidence does not support describing **absolute first-phase STEM placements
since 2017** as one sustained decline. It still does not adjudicate the registered
1997-2026 proposition: the historical programme panel, total programme applications and
the exact age-18 denominator remain pending. A broad
15-24 cohort-proxy sensitivity is now available and reduces the 2017-2026 all-STEM endpoint
change from +9.0% in raw placements to approximately +1.3% after normalisation.

## Proposition 2 — universities are regional; demand pressure accounts for entry-grade differences

This proposition contains three separable empirical questions.

### 2A. Regionality

How strongly is a student's first preference associated with the district from which they apply? The primary evidence is the DGES origin–destination matrix for first preference. Actual placement is secondary because it is constrained by grades and capacity.

### 2B. Demand pressure and entry grades

How much of the variation in the mean grade of placed students and in the last-placed cut-off is explained by applicants per vacancy and first-choice applicants per vacancy, after comparing like courses and years?

The analysis reports both in-sample decomposition and leave-one-year-out predictive performance. “Explains” is therefore given an explicit statistical meaning rather than inferred from a visual correlation.

### 2C. Rankings

When a valid historical ranking series is supplied, does it add explanatory or predictive information for first-choice demand or entry grades beyond course, year, location and demand pressure?

No causal ranking effect is claimed without a separate identification design. Ranking information can influence demand, and demand can mediate any relation between rankings and entry grades.

### v0.3.3 matched-course pilot evidence status

The first programme-level pilot fixes the exact course code 9119 (Engenharia
Informática, Licenciatura) and follows the same 23 institutions in 2018-2020. The
official 2019 and 2020 comparative-course publications overlap in 2019, and all 23
duplicated records reconcile exactly before analysis.

Using total applicants per vacancy, year-specific one-predictor log-demand models
produce cut-off-grade \(R^2\) values of 0.647, 0.559 and 0.743 in 2018, 2019 and
2020. For the mean application grade of placed candidates, the corresponding values
are 0.498, 0.620 and 0.766. Demand is therefore strongly informative in this matched
course, but the pilot does not support describing the relation as nearly complete in
every year.

Institution fixed effects explain substantial persistent between-institution
structure. Adding log applicants per vacancy to institution plus linear-year structure
raises \(R^2\) by 0.020 for the cut-off and 0.018 for the mean placed grade. It also
reduces mean leave-one-year-out RMSE from 9.10 to 7.49 and from 6.51 to 5.13 grade
points respectively.

This evidence is not generalised beyond course 9119. Proposition 2B remains open until
the same contract is applied across a broad programme set. Proposition 2A and 2C are
unchanged and remain pending.

## Proposition 3 — high-performing R&D units and a weakening feeder pipeline

**Public proposition:** high-performing R&D units with a poorer future pipeline will face problems.

This is the least precisely specified proposition, so the project separates observable exposure from future consequences.

### Operationalisation

- **High-performing R&D unit:** primarily an FCT unit rated *Excellent* or *Very Good*. This is an evaluation category, not a direct measure of bibliometric impact.
- **Feeder pipeline:** first-time entrants, first-cycle graduates, second-cycle graduates, doctoral enrolments, doctoral graduates and research personnel in the relevant fields and host institutions.
- **Weakening:** a sustained negative change in one or more pipeline components, reported componentwise.
- **Problem:** where historical outcomes exist, subsequent changes in research staffing, integrated researchers, funding or evaluation. Where they do not, the result is described as exposure or vulnerability rather than an observed consequence.

### Mapping challenge

R&D units are interdisciplinary and can involve several institutions. The project therefore uses an explicit unit–institution–field exposure table rather than assigning each unit to one degree course.

## Evidence language

The paper will distinguish:

- **descriptive:** what changed;
- **predictive:** what improves out-of-sample prediction;
- **associational:** what covaries conditional on observed controls;
- **causal:** reserved for designs with a defensible identification strategy.
