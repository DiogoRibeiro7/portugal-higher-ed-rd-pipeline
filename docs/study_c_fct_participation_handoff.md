# Study C FCT formal-participation handoff

Study C remains fail-closed until the formal participating-institution universe is resolved for every primary-scope R&D unit.

## Why the public results are insufficient

The validated FCT final-results workbook identifies the approved unit, evaluation panel and final rating, but it does not contain the complete participating-institution set. Public information about a management or funding institution is therefore not enough to construct the registered unit weights.

The 2023/2024 evaluation process included unit and research-team registration before the application was submitted. Study C consequently requires the participation structure attached to that evaluation application. A current unit membership list may have changed after submission and must not silently replace the frozen application snapshot.

## Private staging files

Authorised source data remain untracked under `data/private/fct/`.

Prepare:

- `study_c_primary_units.csv` with exactly the 120 primary-scope canonical FCT references;
- `study_c_unit_participation.csv` with one row per formal participating legal entity per unit.

The participation file requires these columns:

- `unit_reference`;
- `participant_institution_id`;
- `participant_institution_name`;
- `source_system`;
- `source_record_id`;
- `snapshot_basis`;
- `integrated_researcher_count`;
- `source_reference`.

`unit_reference` must use the canonical `UID/NNNNN/2023` format. `snapshot_basis` must be `submitted_evaluation_2023_2024_application`.

## Count rule

Integrated-researcher counts are optional at this gate, but availability must be internally coherent within each unit.

For a unit with complete positive counts for every formal participant, the next weighting gate may use count-derived shares. If counts are absent for every participant, the next gate will use equal shares across the complete formal participant set. Partial count availability within a unit is rejected.

Management-institution rows cannot substitute for missing formal participants.

## Validation

Run:

```bash
python scripts/validate_study_c_fct_participation.py \
  data/private/fct/study_c_unit_participation.csv \
  --expected-units data/private/fct/study_c_primary_units.csv \
  --output data/private/fct/study_c_participation_audit.json
```

A valid handoff returns `formal_participation_handoff_validated_weights_pending`. It does not build weights and does not compute any exposure result.

The next gate after a successful handoff is the canonical FCT participant → DGEEC institution concordance and the explicit unit × institution × field weight table, with weights summing to one for every unit.
