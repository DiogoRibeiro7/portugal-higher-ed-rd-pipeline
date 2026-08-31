# Study C RAIDES workbook handoff

This handoff exists because the official DGEEC data page publishes the required 2018/19–2024/25 RAIDES table families, but the client-rendered page does not expose reproducible spreadsheet download targets in the current execution environment.

The raw official workbooks remain private and untracked. Download the seven annual `Inscritos` workbooks and seven annual `Diplomados` workbooks from the canonical DGEEC higher-education data page and stage them under `data/private/raides/study_c/` using the repository-local names below.

| Academic year | Inscritos staging name | Diplomados staging name |
| --- | --- | --- |
| 2018/19 | `inscritos_2018_19.xlsx` | `diplomados_2018_19.xlsx` |
| 2019/20 | `inscritos_2019_20.xlsx` | `diplomados_2019_20.xlsx` |
| 2020/21 | `inscritos_2020_21.xlsx` | `diplomados_2020_21.xlsx` |
| 2021/22 | `inscritos_2021_22.xlsx` | `diplomados_2021_22.xlsx` |
| 2022/23 | `inscritos_2022_23.xlsx` | `diplomados_2022_23.xlsx` |
| 2023/24 | `inscritos_2023_24.xlsx` | `diplomados_2023_24.xlsx` |
| 2024/25 | `inscritos_2024_25.xlsx` | `diplomados_2024_25.xlsx` |

These are local staging names only. They do not assert or guess DGEEC provider filenames.

Run:

```bash
python scripts/validate_study_c_raides_files.py data/private/raides/study_c \
  --output data/private/raides/study_c_byte_audit.json
```

The validator must report all 14 files present and SHA-256 each workbook. Even then, the state remains `validated_bytes_pending_semantic_schema_review`; institution, course, CNAEF/field and cycle variables still require explicit seven-year semantic validation before any Study C exposure is computed.

The separate first-time-entry DGEEC series is not a substitute for the annual `Inscritos` family unless a later prospective gate explicitly changes the registered source contract.
