# Study B rankings and reputation design

## Question

This layer tests the final part of Study B: whether external university-ranking information adds substantial explanatory or predictive information beyond programme/year structure and observed demand pressure.

The analysis is deliberately not framed as a causal effect of rankings. Rankings are treated as imperfect proxies for institutional reputation and visibility.

## Why demand and rankings require separate estimands

A ranking can affect applicant behaviour. Therefore applicants per vacancy may lie on a pathway linking reputation to entry grades. Conditioning on demand changes the question.

The design consequently separates three estimands:

1. **Total ranking association with grades** — programme/year structure plus ranking, without conditioning on demand.
2. **Ranking association with demand** — programme/year structure plus ranking predicting applicants per vacancy.
3. **Residual ranking association with grades conditional on demand** — programme/year structure, demand and ranking together.

The third estimand must not be described as the total effect of ranking or reputation.

## Ranking sources and timing

QS, Times Higher Education and ARWU are eligible providers, but they are analysed separately. Provider scales, bands and methodologies are not pooled into a synthetic rank.

For admission year `t`, only a ranking publication available before the registered application deadline for that competition year is eligible. Future ranking editions are never back-cast into earlier admission decisions.

Exact ranks may be used ordinally when officially published. Rank bands remain categorical in the primary analysis. Band midpoints are not substituted in the primary model.

Missing ranking coverage remains missing. An unranked institution is not assigned rank zero or an artificial bottom rank.

## Institutional scope

The programme-level Study B data include universities and polytechnics. External global rankings primarily rank parent universities. The primary ranking analysis is therefore restricted to rows that can be mapped explicitly to an eligible parent university.

Mappings are concordance-driven only. No fuzzy name matching is allowed in the release analysis. Polytechnic establishments are excluded from the primary ranking estimand rather than being given a fabricated university ranking.

Coverage is reported at both parent-institution and programme-establishment-row level.

## Model sequence

For each provider and primary grade outcome, compare:

\[
M_0: y = f(\text{programme},\text{year}),
\]

\[
M_R: y = f(\text{programme},\text{year}) + \text{ranking},
\]

\[
M_D: y = f(\text{programme},\text{year}) + \log(\text{applicants/vacancy}),
\]

and

\[
M_{DR}: y = f(\text{programme},\text{year}) + \log(\text{applicants/vacancy}) + \text{ranking}.
\]

The primary ranking comparisons are the incremental performance of `M_R` relative to `M_0`, and `M_DR` relative to `M_D`.

A separate model uses applicants per vacancy as the outcome to quantify the association between ranking and observed demand pressure.

## Validation

In-sample R-squared is descriptive only. The primary predictive validation is **leave-one-parent-institution-out**. All programme rows belonging to one parent university are held out together.

This prevents the same institutional ranking value from appearing in both training and test data through different courses or establishments.

The principal predictive quantities are out-of-institution RMSE and MAE, together with the change obtained by adding ranking to the relevant baseline.

## Interpretation

Evidence that ranking adds little after demand would mean exactly that: limited residual information after conditioning on contemporaneous demand and programme/year structure in the ranked-university subset. It would not show that institutional reputation is irrelevant, because reputation may already be reflected in demand.

Similarly, a strong ranking-to-demand association would support the possibility that demand is partly a channel through which institutional reputation is expressed, but this design does not identify mediation causally.

The ranking analysis is therefore descriptive and predictive throughout.
