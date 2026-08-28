# Data sources

## DGES — Concurso Nacional de Acesso

DGES is the core source for Studies A and B. The official national-access archive currently lists annual statistics from 1997 to 2025. For standard vintages it exposes first-phase institution–programme statistics, capacity/placement tables and geographic mobility documents.

The repository does not treat every year as having an identical file layout. It uses three registered modes: archive discovery for 1997–2003, the verified `statcol`/`statce` family for 2004–2025, and a separate current-results adapter for 2026.

Detailed pair sheets provide total applicants, first-choice applicants, placements and grade summaries. Vacancy/cut-off tables independently provide initial places, placements and last-placed grades. Because placement counts occur in both source families, they form a useful ingestion consistency check.

Mobility documents require special treatment. Recent files are comparative and carry matrices for both the document year and the preceding competition year. Older origin labels can also represent CAE/GAES access areas rather than districts. The canonical schema therefore preserves both `year` and `source_document_year`, and uses `origin_area` rather than assuming that every origin is a district.

The 2026 first-phase placement page currently exposes Excel and PDF cut-off results. It is registered as a partial current vintage; the project does not infer that the final 2026 annual-statistics bundle has the same structure before DGES publishes it.

### Study A broad-area publication tables

The v0.3.1 medium-run layer uses official complete broad-area first-phase tables for
2017, 2018 and 2020-2026. The 2017 source numbers this table as `Quadro XII`; the
later locked vintages use `Quadro V`. The source manifest records this numbering
rather than assuming that table identifiers are stable across vintages.

The official 2019 first-phase archive was audited in v0.3.2. Its standard index lists
summary, establishment/course comparisons, mobility, cut-offs and pair statistics, but no
comparable complete broad-area placement table. National 2019 counts remain useful as
controls, but they do not identify field composition and are not used to fill the gap. See
[`dges_2019_archive_audit.md`](dges_2019_archive_audit.md).

See [`dges_ingestion.md`](dges_ingestion.md) for parser and provenance rules and
[`study_a_medium_run.md`](study_a_medium_run.md) for the publication-table analysis.

## DGEEC — RAIDES

RAIDES is the official register of students enrolled and graduating from Portuguese higher-education institutions. It is the backbone for the education-pipeline stages beyond the access competition: first-time enrolment, first-cycle output, master's output and doctoral activity.

Public summary tables are sufficient for some national/field trends. Institution-level or programme-level work should use the most granular lawful table available and record the extraction route.

## DGEEC — IPCTN and doctorate-holder statistics

IPCTN provides official R&D personnel and institutional research statistics. The doctorate-holder survey provides complementary information on the stock and labour-market location of doctorate holders.

These sources help distinguish a weak educational pipeline from changes in the employment destination of highly qualified researchers.

## FCT — R&D Units

FCT periodically evaluates R&D units using international panels and publishes unit-level information and evaluation results. The 2023/2024 evaluation covers activity in 2018–2023 and plans for 2025–2029.

The project uses FCT ratings as performance categories. It does not relabel them as a direct measure of “impact”. Where impact is of interest, a separate bibliometric or grant-output measure must be introduced.

## INE — population

Official population series are used to construct demographic-normalised access rates. The primary empirical series always retain the raw counts and shares, so conclusions do not depend on one denominator choice.

The preferred Study A denominator is the population aged exactly 18. Until that single-age series is source-locked, v0.3.2 reports a sensitivity based on the INE population aged 15-24 disseminated by PORDATA. Dividing that ten-year band by ten gives an explicitly labelled average single-year cohort proxy. Competition year `t` uses the population reference for `t-1`. The proxy is never described as an age-18 count and is not promoted to a primary estimand. See [`study_a_demography.md`](study_a_demography.md).

## DGES comparative course statistics (`StatsCurso`)

The comparative course-statistics PDFs report, by course and establishment, the current
and previous first-phase year side by side. Their columns include vacancies, total
applicants, first-choice applicants, total and first-choice placements, the last-placed
grade and mean grade components. This makes them useful both as a compact programme
panel source and as an internal cross-vintage consistency check.

Version 0.3.3 uses `StatsCurso19.pdf` (2018-2019) and `StatsCurso20.pdf` (2019-2020)
for the exact course code 9119. The repeated 2019 observations are retained at the
source layer and reconciled before the analytical panel is built. Provider bytes are
not bundled in this release; the committed values are labelled as curated
transcriptions from the official publications.

## Rankings

Rankings are optional and secondary. The code accepts a standardised CSV/Parquet contract, but the repository does not redistribute provider data. Historical methodology changes, tied ranks and rank bands must be preserved rather than coerced into false precision.

## Provenance requirements

Each raw source must have a machine-readable receipt containing its URL, retrieval time, byte size and SHA-256 digest. When a canonical observation requires more than one raw source, the individual source hashes remain separate and a deterministic combined lineage fingerprint is added. A combined fingerprint is never described as though it were the hash of a single provider file.
