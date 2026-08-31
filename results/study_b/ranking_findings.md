# Study B ranking and reputation findings

## Registered predictive result

The ranking analysis was executed only after the provider coverage, historical-value, LOPO ranking-support, categorical-reference, and structural-support gates were frozen.

All model comparisons use identical provider-ranked training rows and identical ranking/structure-supported held-out observations within each pair. Negative `delta_rmse` or `delta_mae` means the model including ranking predicts better than its paired baseline.

## Times Higher Education

Times Higher Education is the only provider with broad enough support for a strong out-of-institution comparison: 112 of 116 eligible programme rows are scored across all 11 eligible parents (96.55% row support).

Without conditioning on demand, adding THE rank bands improves both grade outcomes:

- last placed general-contingent grade: RMSE 19.914 -> 18.240 (`delta_rmse = -1.673`, -8.40%); MAE 15.740 -> 14.507;
- mean placed application grade: RMSE 15.435 -> 14.051 (`delta_rmse = -1.383`, -8.96%); MAE 12.324 -> 11.749.

Ranking also modestly improves demand prediction:

- applicants per vacancy: RMSE 3.503 -> 3.369 (`delta_rmse = -0.135`, -3.85%); MAE 2.876 -> 2.689.

After conditioning on contemporaneous demand, however, the incremental THE gain in grade prediction disappears:

- last placed grade: RMSE 13.080 -> 13.090 (`delta_rmse = +0.010`);
- mean placed grade: RMSE 11.087 -> 11.114 (`delta_rmse = +0.028`).

MAE also worsens slightly in both demand-conditioned comparisons.

The appropriate interpretation is therefore that THE ranking information carries some total predictive association with grades, and some association with observed demand pressure, but contributes essentially no residual out-of-institution predictive information for grades once contemporaneous demand is included. This is descriptive/predictive evidence, not causal mediation evidence.

## QS

QS has substantially narrower usable LOPO support: 30 of 54 eligible programme rows across four of six ranked parents are scored (55.56%). Twenty-four rows are excluded because their ranking representation is unsupported in the corresponding held-out fold.

Adding QS ranking information substantially worsens both grade outcomes, with or without demand:

- `M0 -> MR`: grade RMSE increases by 6.635 and 7.076 points for the two registered grade outcomes;
- `MD -> MDR`: grade RMSE increases by 5.950 and 6.254 points.

Demand prediction shows a small RMSE improvement (-0.139) but a small MAE deterioration (+0.055). Given the narrow support and mixed demand metric, this should not be presented as robust incremental predictive value.

## ARWU

ARWU has similarly narrow usable support: 27 of 47 eligible programme rows across three of six ranked parents are scored (57.45%). Seventeen rows are ranking-unsupported and three additional rows are structurally unsupported.

The grade results are mixed and weak:

- without demand, ranking worsens both registered grade RMSEs (+0.931 and +0.167);
- with demand, cut-off RMSE improves by 0.724 but its MAE worsens by 0.744;
- the demand-conditioned mean-grade model worsens on both RMSE and MAE;
- demand prediction worsens on both metrics.

With only three supported parents, no broad generalisation should be made from the isolated cut-off RMSE improvement.

## Study B conclusion

Across the three preregistered providers, the strongest interpretable result comes from THE because it retains nearly the full parent-university sample.

The evidence is consistent with:

1. institutional ranking/reputation information being associated with grades and demand in the broad THE sample;
2. contemporaneous demand absorbing essentially all of the incremental THE grade-prediction gain;
3. QS and ARWU providing too little stable incremental predictive value, with much narrower LOPO support.

This does **not** establish that reputation is causally mediated by demand, nor that rankings measure reputation without error. It shows that, in the registered five-programme 2018-2020 panel, external ranking information adds little residual predictive information for entry grades after observed demand is included.
