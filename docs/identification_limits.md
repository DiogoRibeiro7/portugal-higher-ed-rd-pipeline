# Identification limits

This project can answer several questions well with observational administrative data, but it should not overstate what those data identify.

## Entry grades and demand

The cut-off grade is an allocation outcome. With more eligible applicants per vacancy, the selected order statistic generally rises even if preferences and institutional quality are unchanged. Consequently:

- a strong applicants/vacancy–cut-off relationship can be mechanically expected;
- it is still useful for explaining/predicting observed grades;
- it is not, by itself, a causal estimate of “demand causing quality”.

The v0.3.3 matched-course pilot removes one major source of compositional variation by
holding course code 9119 fixed. It does not remove persistent institution differences,
location, applicant composition or other time-varying factors. Cross-sectional
\(R^2\), institution fixed effects and leave-one-year-out prediction are therefore
reported as complementary descriptions rather than as causal identification.

## Rankings and reputation

Rankings can affect demand, but demand can mediate the relation between rankings and grades. Controlling for applicants/vacancy while asking whether rankings “matter” can therefore remove part of the pathway of interest.

The project reports two distinct specifications:

1. ranking association with first-choice demand;
2. ranking incremental association with grades after demand.

Neither is causal without exogenous ranking variation or another credible design.

## Geography

A high same-district share is consistent with regionality but can reflect distance, housing costs, programme availability and family resources. Regionality is therefore a descriptive pattern, not a single behavioural cause. Historical CAE/GAES access areas also create a measurement-comparability problem: they are not forced into district labels, and diagonal statistics must report the share of flows whose origin geography is genuinely comparable.

## R&D pipeline

A reduction in STEM entrants need not translate one-for-one into fewer researchers. International students, migration, field switching, private-sector wages, research careers and funding conditions all intervene.

With only a small number of FCT evaluation waves, linking pipeline changes to later unit ratings is especially vulnerable to confounding and low statistical power. The project therefore treats prospective pipeline exposure as a separate result from realised unit performance.
