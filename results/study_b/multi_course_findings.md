# Study B multi-course demand/selectivity results

## Scope

This evidence layer applies the frozen v0.3.4 Study B design to five exact DGES programme identities: 9081 Economia, 9119 Engenharia Informática, 9147 Gestão, 9219 Psicologia and 9500 Enfermagem. The comparison covers the first phase of the 2018, 2019 and 2020 national access competitions using the official DGES `StatsCurso19` and `StatsCurso20` comparative tables.

The provider PDF bytes are not bundled. The committed CSV shards are curated transcriptions tied to the registered official URLs and source-page labels; they are not raw-provider archives.

## Reconciliation and coverage

The source layer contains 348 rows for 87 programme-establishment units. Every unit appears as 2018 and 2019 in `StatsCurso19` and as 2019 and 2020 in `StatsCurso20`. All 87 duplicated 2019 observations agree exactly across the two source vintages on the registered count and grade measures. Deduplication therefore produces 261 canonical programme-establishment-year observations.

All five programmes clear the frozen six-establishment coverage gate: Economia has 13 stable establishments, Engenharia Informática 23, Gestão 22, Psicologia 8 and Enfermagem 21. Stable-offering selection uses source coverage only and precedes model-completeness checks.

The model-complete panel contains 86 of the 87 stable establishments, or 258 programme-establishment-year observations. The only excluded unit is Economia at the University of the Azores. In 2018 the table records one placed candidate and does not publish a general-contingent cut-off. The missing value is preserved and is not imputed.

## Registered association result

Within each programme and year, the registered descriptive model is

\[
y_{ipt}=\alpha_{pt}+\beta_{pt}\log\left(\frac{\mathrm{applicants}_{ipt}}{\mathrm{vacancies}_{ipt}}\right)+\varepsilon_{ipt}.
\]

For the general-contingent cut-off, the 15 programme-year cells have median \(R^2=0.598\) and interquartile range \([0.489,0.669]\). Ten of the 15 cells have \(R^2\geq0.50\), none reaches \(R^2\geq0.80\), and the observed range is 0.320 to 0.743.

For the mean application grade of placed candidates, median \(R^2=0.552\) and the interquartile range is \([0.419,0.580]\). Nine of the 15 cells have \(R^2\geq0.50\), none reaches \(R^2\geq0.80\), and the range is 0.186 to 0.766.

All 30 fitted log-demand coefficients are positive. Demand pressure is therefore consistently associated with higher entry grades in this registered panel, but its explanatory strength is heterogeneous. Enfermagem is particularly informative: its cut-off \(R^2\) values are 0.320, 0.323 and 0.484 across 2018-2020, whereas Engenharia Informática gives 0.647, 0.559 and 0.743.

## Interpretation boundary

The registered evidence supports the statement that applicants per vacancy is an important descriptive predictor of entry grades across multiple matched programmes. It does not support describing the ratio as explaining cross-institution differences almost completely under the frozen 0.80 benchmark.

This is not yet an analysis of regionality or university rankings. Nothing here establishes that rankings are irrelevant, because reputation may affect demand and demand may mediate part of any association between reputation and entry grades. The reported coefficients and \(R^2\) values are descriptive and predictive summaries, not causal effects or sampling-inference claims.
