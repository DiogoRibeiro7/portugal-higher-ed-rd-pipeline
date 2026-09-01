# Study C unit–institution–field weight gate

This gate converts a validated formal FCT participation handoff into explicit institution weights for the frozen Study C primary population. It does not estimate feeder trends or unit exposure.

## Inputs

Three private inputs are required:

1. `data/private/fct/study_c_unit_participation.csv`, validated against the 2023/2024 evaluation-application snapshot contract;
2. `data/private/fct/study_c_participant_dgeec_concordance.csv`, containing one explicit participant-institution to DGEEC institution mapping per formal participant;
3. `data/private/fct/study_c_primary_units.csv`, containing the canonical `UID/NNNNN/2023` reference and frozen ISCED-F scope for each primary unit.

The participant concordance must contain:

- `participant_institution_id`;
- `participant_institution_name`;
- `dgeec_institution_code`;
- `dgeec_institution_name`;
- `mapping_basis`;
- `source_reference`.

Fuzzy-name matching is not accepted as a production mapping. Normalised names may be useful during manual candidate review, but the final concordance must contain the explicit accepted DGEEC identifier.

## Weight rule

For unit \(u\) and formal participating institution \(h\), the institution share is

\[
w_{u,h}=\frac{n_{u,h}}{\sum_j n_{u,j}}
\]

when complete positive integrated-researcher counts \(n_{u,h}\) are available for every formal participant in that unit.

If counts are unavailable for all participants, the registered fallback is

\[
w_{u,h}=\frac{1}{H_u},
\]

where \(H_u\) is the complete number of formal participating institutions.

Mixed count availability is invalid. Management-only institutions may not substitute for omitted participants.

Each primary unit has one frozen broad feeder field from the canonical FCT panel→ISCED-F crosswalk. Therefore the final gate output is a unit×institution×field table satisfying

\[
\sum_{h,f} w_{u,h,f}=1
\]

for every unit.

## Missing RAIDES support

The weight table represents the organisational exposure structure. It is not conditioned on whether RAIDES contains an eligible institution×field series.

A formal participant must therefore **not** be dropped merely because its downstream feeder series is unsupported. The weight is retained. Later exposure calculations must report that component as unavailable rather than renormalising the remaining institutions to one.

## Command

```bash
python scripts/build_study_c_unit_weights.py
```

With complete validated private inputs, the command writes:

`results/study_c/unit_institution_field_weights.csv`

If any required private input is absent, the command exits non-zero and does not create a substitute result.

## Scientific boundary

This gate produces organisational weights only. It does not compute institution feeder trends, unit exposure vectors, weakening-component counts, rating-group comparisons or a composite vulnerability score.
