# Study A demographic normalisation

## Purpose

Study A registers demographic normalisation because absolute placement counts can move with the size of the relevant entry-age population. The preferred denominator is therefore the resident population aged exactly 18.

The exact denominator is now source-locked from INE indicator `0001223`, **População residente (Série longa, início 1970 - N.º) por Sexo e Idade; Anual - INE, Estimativas anuais da população residente**. The released slice is Portugal (`PT`), total sex (`T`, labelled `HM`) and exact age 18 (metadata category `224`, labelled `18 anos`).

## Source and timing

The source-locked exact-age values are stored in:

`data/curated/demography/pt_population_age_18_2016_2025.csv`.

For CNA competition year \(t\), the demographic reference is population year \(t-1\). The 2016 population therefore normalises the 2017 competition and the 2025 population normalises the 2026 competition. Under this frozen convention, the current 2017-2026 medium-run panel requires exact-age values for 2016-2025.

The source series is validated against the official INE dimensions and metadata. No age value is inferred or interpolated.

INE identifies a methodological break between 2020 and 2021: annual resident-population estimates are census-based through 2020 and administrative-base from 2021 onward. Any path or trend spanning that boundary must carry this comparability caveat explicitly.

## Exact age-18 rate

For competition year \(t\), define

\[
R_t^{18}
=
1000\frac{P_t}{N_{18,t-1}},
\]

where \(P_t\) is the observed first-phase placement count and \(N_{18,t-1}\) is the resident population aged exactly 18 in the preceding calendar year.

The exact-age outputs are stored in:

- `results/study_a/age18_stem_metrics.csv`;
- `results/study_a/age18_component_metrics.csv`;
- `results/study_a/age18_endpoint_comparison.csv`.

The committed outputs are covered by a release-data regression that rebuilds them from the source-locked population and Study A medium-run inputs.

## Endpoint result

Between the observed 2017 and 2026 endpoints, registered all-STEM placements increase by approximately 9.0%.

The exact age-18-normalised all-STEM rate moves from approximately

\[
126.1\rightarrow137.5
\]

placements per 1,000 residents aged 18, an endpoint increase of approximately 9.1%.

The exact-age component endpoint changes are approximately:

- group 05, natural sciences, mathematics and statistics: -6.7%;
- group 06, information and communication technologies: +60.1%;
- group 07, engineering, manufacturing and construction: +11.1%;
- all registered STEM: +9.1%.

The exact entry-age denominator therefore does not reproduce the strong attenuation observed with the broader 15-24 cohort proxy.

## Broad-cohort sensitivity

The earlier sensitivity remains useful as a distinct demographic-scale comparison. It uses the INE resident population aged 15-24 disseminated by PORDATA and divides the ten-year age band by ten:

\[
C_t^{\mathrm{proxy}}
=
\frac{N_{15:24,t-1}}{10}.
\]

The resulting rate is

\[
R_t^{\mathrm{proxy}}
=
1000\frac{P_t}{C_t^{\mathrm{proxy}}}.
\]

This is an average single-year cohort proxy, not the population aged 18. Under that broader denominator, the all-STEM endpoint change is approximately +1.3%, compared with +9.1% under the exact age-18 denominator.

The contrast is scientifically meaningful: the 15-24 proxy measures broad young-adult population scale, whereas the exact-age rate measures placement volume relative to the registered entry-age cohort.

## Interpretation boundary

The demographic normalisations do not replace the co-primary raw count and placement-share margins, and they do not solve the missing 2019 broad-area observation.

The empirical margins remain distinct:

- raw placements describe realised absolute volume;
- placement share describes STEM relative to the whole CNA allocation;
- the exact age-18 rate describes placement volume relative to the registered entry-age cohort;
- the 15-24 cohort-proxy rate is retained only as a broader demographic sensitivity.

None of these transformations authorises a causal interpretation of placement changes.
