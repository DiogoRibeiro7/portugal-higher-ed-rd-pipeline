# Study A demographic cohort-proxy sensitivity

## Purpose

Study A registers demographic normalisation because an absolute placement count can move when the size of the relevant entry-age population moves. The preferred denominator is the resident population aged exactly 18.

The exact source is now identified and registered as INE indicator `0002721`, **População média anual residente (Série longa, início 1971 - N.º) por Sexo e Idade; Anual**, using the Portugal, total-sex, age-18 slice. Its values are not yet source-locked in this release. The current empirical sensitivity therefore continues to use the deliberately weaker 15-24 cohort proxy rather than silently promoting an unacquired series into the calculations.

## Source and timing

The released sensitivity uses the INE resident population aged 15-24 disseminated by PORDATA. PORDATA identifies INE as the source entity and reports the series through 2025. The release uses values from 2016 through 2025.

For CNA competition year \(t\), the demographic reference is the population reported for the preceding calendar year \(t-1\). This aligns the 2016 population reference with the 2017 competition and the 2025 population reference with the 2026 competition. Under this registered lag convention, the exact-age series therefore needs 2016-2025 values to normalise the current 2017-2026 medium-run panel; a 2026 population value is not required for that comparison.

The released proxy source values are stored in:

`data/curated/demography/pt_population_15_24_2016_2025.csv`.

They are curated published values rather than bundled provider bytes. No provider-file hash is invented.

The preferred exact-age source is registered in `config/source_registry.yml`. INE indicator `0002721` has long historical coverage, but the repository does not yet contain its age-18 values because the direct INE JSON endpoint was not reliably reachable from the automated acquisition environment. An official export or a reproducible dissemination mirror must be source-locked before those values enter release calculations.

The exact-age series also carries a comparability caveat around 2020-2021: the dissemination metadata identifies a change in the population-estimation basis from the pre-2021 census-based estimates to the post-2021 administrative-base estimates. Any exact-age trend analysis spanning that boundary must record it explicitly and must not interpret a discontinuity there automatically as demographic change.

## Cohort proxy

The 15-24 band spans ten integer ages. Define

\[
C_t^{\mathrm{proxy}}
=
\frac{N_{15:24,t-1}}{10}.
\]

This is an **average single-year cohort proxy**. It is not the number of residents aged 18 and is never labelled as such.

The sensitivity rate is

\[
R_t^{\mathrm{proxy}}
=
1000\frac{P_t}{C_t^{\mathrm{proxy}}},
\]

where \(P_t\) is the observed first-phase placement count.

This denominator is useful for asking whether raw placement growth is larger or smaller than broad changes in the young-adult population. It is not suitable for fine causal interpretation of access propensity.

## Endpoint result

The demographic reference population rises from 1,101,839 in 2016 to 1,185,234 in 2025, an increase of approximately 7.6%. Over the corresponding 2017-2026 CNA endpoints, registered STEM placements rise by 9.0%.

The cohort-proxy rate therefore moves from approximately

\[
126.4\rightarrow128.1
\]

placements per 1,000 average single-year cohort equivalents, an endpoint increase of about 1.3%.

The component-normalised endpoint changes are approximately:

- group 05, natural sciences, mathematics and statistics: -13.3%;
- group 06, information and communication technologies: +48.7%;
- group 07, engineering, manufacturing and construction: +3.2%;
- all registered STEM: +1.3%.

The broad demographic adjustment therefore materially reduces the apparent all-STEM endpoint increase without reversing it. It also sharpens the component heterogeneity.

## Interpretation boundary

The sensitivity does not replace the co-primary raw count and placement-share margins. It also does not solve the missing 2019 broad-area observation. The main scientific statements remain separate:

- raw placements describe realised absolute volume;
- placement share describes STEM relative to the whole CNA allocation;
- the cohort-proxy rate describes placement volume relative to a broad young-adult population scale.

The exact age-18 denominator is no longer an unidentified source problem: the official indicator and target slice are registered. It remains an **acquisition and source-locking** problem. Until those values are reproducibly captured and their 2020-2021 methodological break is carried into the analysis, the released 15-24 proxy remains the only demographic normalisation used in reported results.
