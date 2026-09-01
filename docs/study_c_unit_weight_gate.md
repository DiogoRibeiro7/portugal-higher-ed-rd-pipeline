# Study C unit-institution-field weight gate

This gate converts a validated formal FCT participation handoff into explicit institution weights for the frozen Study C primary population. It does not estimate feeder trends or unit exposure.

## Inputs

Three private inputs and one committed crosswalk are required:

1. `data/private/fct/study_c_unit_participation.csv`, validated against the 2023/2024 evaluation-application snapshot contract;
2. `data/private/fct/study_c_participant_dgeec_concordance.csv`, containing one explicit reviewed classification per formal participant;
3. `data/private/fct/study_c_primary_units.csv`, containing the canonical `UID/NNNNN/2023` reference and canonical FCT evaluation-panel label for each primary unit;
4. `data/curated/fct/study_c_panel_isced_crosswalk.csv`, which maps that canonical panel label to the frozen broad ISCED-F scope.

The private primary-unit registry does not supply `isced_f_scope`. The builder derives it from the committed panel crosswalk. This keeps the field definition under the reviewed repository contract rather than duplicating it in a private staging file.

The participant concordance must contain:

- `participant_institution_id`;
- `participant_institution_name`;
- `mapping_status`;
- `dgeec_institution_code`;
- `dgeec_institution_name`;
- `mapping_basis`;
- `source_reference`.

`mapping_status` is one of:

- `mapped_to_dgeec_establishment`;
- `not_higher_education_establishment`.

For `mapped_to_dgeec_establishment`, both `dgeec_institution_code` and `dgeec_institution_name` must be nonblank. For `not_higher_education_establishment`, both DGEEC fields must be blank. This prevents non-higher-education participants from being forced into a fabricated RAIDES establishment mapping.

The production concordance join uses `participant_institution_id` only. Participant names from the participation export and reviewed concordance are retained as separate audit labels, so benign spelling or legal-name differences do not invalidate an explicit ID mapping. Fuzzy-name matching is not accepted as a production mapping.

## Weight rule

For unit u and formal participating institution h, the institution share is proportional to the integrated-researcher count when complete positive counts are available for every formal participant in the unit.

If counts are unavailable for all participants, the registered fallback is an equal share across the complete formal participant set.

Mixed count availability is invalid. Management-only institutions may not substitute for omitted participants. Every unit must have weights summing to one within the registered tolerance.

Each primary unit has one frozen broad feeder field derived from its canonical FCT panel via the committed panel-to-ISCED-F crosswalk. The final gate output is therefore an explicit unit x institution x field table.

## Missing RAIDES support

The weight table represents the organisational exposure structure. It is not conditioned on whether RAIDES contains an eligible institution x field series.

A formal participant must not be dropped merely because its downstream feeder series is unsupported or because it is not a higher-education establishment. The weight is retained. Later exposure calculations must report that component as unavailable rather than renormalising the remaining institutions to one.

## Command

```bash
python scripts/build_study_c_unit_weights.py
```

With complete validated private inputs, the command writes `results/study_c/unit_institution_field_weights.csv`.

If any required private input is absent, the command exits non-zero and does not create a substitute result.

## Scientific boundary

This gate produces organisational weights only. It does not compute institution feeder trends, unit exposure vectors, weakening-component counts, rating-group comparisons or a composite vulnerability score.
