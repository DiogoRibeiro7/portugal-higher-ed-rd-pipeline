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

The remaining smaller registered parents are retained as not covered only where historical evidence is consistent with non-membership. Provider data themselves are not redistributed in this repository.

## Verified THE coverage pattern

THE is materially broader than QS in the relevant period.

Historical sources verify that Universidade da Beira Interior and Universidade de Tras-os-Montes e Alto Douro were already present in the overall THE World University Rankings in 2018-2020. Universidade de Evora is verified in the 2018 and 2019 editions. A 2021 Portuguese higher-education data project using THE 2020/2021 data also records overall THE coverage for Universidade do Algarve, Universidade da Beira Interior, ISCTE, Universidade do Minho and the core Lisbon/Porto/Coimbra/Aveiro/NOVA universities, while explicitly noting that UTAD and Evora were present in the 2020 publication but absent from the 2021 publication.

Universidade dos Acores is not observed in the overall THE ranking until much later (2024 in the recovered historical series), so it is not eligible as covered in the frozen 2018-2020 editions. Historical overall coverage for Universidade da Madeira was not verified during this audit and must remain unresolved rather than being silently coded as unranked.

## ARWU status

The eligible overall ARWU editions are 2017, 2018 and 2020. Historical provider pages do not expose sufficiently reproducible complete Portugal membership through the interfaces available to this audit, and the repository contract prohibits redistributing provider ranking tables.

ARWU coverage therefore remains `unresolved` at this gate. This is a data-provenance limitation, not evidence of non-coverage. No ARWU model may be fitted until the provider/year parent membership has been verified from an admissible source.

## Common-sample requirement

Coverage differences are large enough that incremental ranking comparisons must use a common sample.

For a provider-specific comparison:

- `M0` versus `MR` must be evaluated on exactly the rows for which that provider has a ranking observation;
- `MD` versus `MDR` must likewise use the same ranked rows with valid positive demand;
- a lower RMSE from a ranking model cannot be interpreted as incremental ranking information if the baseline was fitted or evaluated on a different row set.

This requirement does not alter the registered models. It makes their comparison well-defined under incomplete provider coverage.

## Scientific boundary

This audit contains no ranking coefficients, no ranking values, and no model results. Its purpose is to determine whether each provider supplies enough historically valid institutional coverage to support the preregistered analysis without hiding sample selection.