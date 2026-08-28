# Paper

Compile from this directory with:

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Rebuild the empirical inputs and figures first:

```bash
poetry run python scripts/build_study_a_recent.py
poetry run python scripts/build_study_a_medium_run.py
poetry run python scripts/build_study_a_demographic.py
```

The current paper reports the medium-run Study A evidence and its broad-cohort
demographic sensitivity. It does not treat either the 15-24 cohort proxy or the
2017-2026 broad-area window as a substitute for the registered exact age-18 and
1997-2026 programme-level analyses.
