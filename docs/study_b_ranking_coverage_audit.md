# Study B historical ranking coverage audit

## Scope

This audit is deliberately separated from the ranking models. It asks only which of the 13 registered parent universities can be verified as covered by each frozen provider edition before any coefficient or predictive comparison is calculated.

The audit follows the contracts frozen in PRs #7-#9:

- provider-specific analysis only;
- explicit parent-university concordance only;
- publication before the first-phase application deadline;
- no future-edition back-casting;
- no fabrication of parent rankings for standalone nursing schools or polytechnics;
- no inference that an institution is unranked merely because a historical provider page could not be recovered.

## Verified QS coverage pattern

The frozen QS overall editions for admission years 2018-2020 are QS 2019, QS 2020 and QS 2021.

Historical and institutional evidence supports a stable core of six registered parents in those editions:

- Universidade de Lisboa;
- Universidade do Porto;
- Universidade NOVA de Lisboa;
- Universidade de Coimbra;
- Universidade de Aveiro;
- Universidade do Minho.

Several exclusions can be verified independently rather than inferred from a missing search hit. Universidade do Algarve states that its first inclusion in the overall QS World University Rankings was the 2026 edition. Universidade da Beira Interior states that its first inclusion was the 2027 edition. ISCTE documents entry into QS World University Rankings by Subject in 2019 rather than the overall ranking. These institutions must therefore not be treated as covered by QS overall in the frozen 2019-2021 editions.

Provider ranking tables themselves are not redistributed in this repository.

## Verified THE coverage pattern

THE is materially broader than QS, but the coverage set is edition-specific rather than constant over 2018-2020.

For THE 2018, the historical annual table verifies nine registered parents: Universidade do Porto, Universidade de Aveiro, Universidade de Coimbra, Universidade de Lisboa, Universidade NOVA de Lisboa, Universidade da Beira Interior, Universidade do Minho, Universidade do Algarve and ISCTE. Universidade de Tras-os-Montes e Alto Douro and Universidade de Evora are not present in that edition and are therefore not coded as covered for 2018 admissions.

For THE 2019 and THE 2020, historical evidence verifies eleven registered parents, adding UTAD and Evora to the 2018 set. Universidade dos Acores is a later entrant and is not covered in the frozen editions. Universidade da Madeira remains unresolved in all three years rather than being silently coded as unranked.

The resulting verified programme-row coverage is therefore 32/52 for 2018 and 42/52 for both 2019 and 2020, with five Madeira rows unresolved in each year.

## Verified ARWU coverage pattern

The eligible overall ARWU editions are 2017, 2018 and 2020. Historical University of Porto ARWU tables provide an admissible reconstruction of Portuguese membership under the repository contract.

The verified parent counts are:

- ARWU 2017 / 2018 admissions: five parents;
- ARWU 2018 / 2019 admissions: four parents;
- ARWU 2020 / 2020 admissions: six parents.

Earlier tables separately identify candidate institutions outside the Top 500. Those candidate groups are not promoted to ranking bands. In particular, NOVA in ARWU 2017 and NOVA plus Coimbra in ARWU 2018 are not treated as ranked observations.

## Common-sample requirement

Coverage differences are large enough that incremental ranking comparisons must use a common sample.

For a provider-specific comparison:

- `M0` versus `MR` must be evaluated on exactly the rows for which that provider has a ranking observation;
- `MD` versus `MDR` must likewise use the same ranked rows with valid positive demand;
- a lower RMSE from a ranking model cannot be interpreted as incremental ranking information if the baseline was fitted or evaluated on a different row set.

This requirement does not alter the registered models. It makes their comparison well-defined under incomplete provider coverage.

## Scientific boundary

This audit contains no ranking coefficients and no ranking-model results. Its purpose is to determine whether each provider supplies enough historically valid institutional coverage to support the preregistered analysis without hiding sample selection.