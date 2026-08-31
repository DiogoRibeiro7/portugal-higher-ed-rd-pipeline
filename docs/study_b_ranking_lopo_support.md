# Study B LOPO support rule for ranking predictors

## Purpose

The registered ranking analysis uses leave-one-parent-institution-out (LOPO) validation and keeps official rank bands categorical. Those two choices create a support problem that must be resolved before any predictive result is inspected.

If a held-out parent carries an official rank-band level that is absent from the training parents, the coefficient for that band is unidentified in that fold. Reindexing the test design matrix to the training columns would otherwise replace the unseen band by an all-zero dummy vector and silently make it indistinguishable from the reference category.

That behaviour is not accepted as a valid out-of-institution prediction.

## Frozen support rule

For a LOPO fold that includes ranking:

- a banded test row is supported only when its exact published band is observed in at least one training row;
- an exact-rank test row is supported only when the training data contain at least two distinct exact published ranks;
- unsupported test rows are reported explicitly and excluded from predictive scoring;
- unsupported rows are never recoded to another band, a midpoint, rank zero, or the reference category.

The rule concerns predictive support only. It does not alter the underlying historical coverage table and it does not relabel an institution as unranked.

## Common-sample comparisons

Incremental predictive comparisons must use identical training and test samples within each provider and outcome.

For `M0` versus `MR`:

1. construct the provider-ranked complete-case sample;
2. hold out one parent;
3. determine the ranking-supported test rows using the rule above;
4. fit both `M0` and `MR` on the same ranked training rows;
5. score both models on the same supported held-out rows.

For `MD` versus `MDR`, apply the same procedure after additionally requiring positive observed applicants per vacancy.

Therefore a reported RMSE or MAE difference is a model difference, not a sample-composition difference.

## Reporting

Every predictive comparison must report:

- number of eligible provider-ranked rows;
- number of eligible parents;
- supported held-out rows scored;
- unsupported held-out rows;
- supported held-out parents;
- RMSE and MAE for both models on the identical supported observations.

If no supported held-out observations remain, the comparison fails closed rather than returning a numerical performance result.

## Scientific boundary

This rule is frozen before the first provider-specific ranking result is calculated. It changes neither the registered ranking representation nor the substantive estimands. It only prevents an unidentified categorical level from being silently treated as an observed reference level during LOPO validation.
