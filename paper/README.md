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
poetry run python scripts/build_study_a_age18.py
poetry run python scripts/build_study_a_demographic.py
```

The current paper reports the completed source-locked Study A empirical phase for the
2017-2026 window, with 2019 retained as an unobserved field-composition year. The
primary demographic normalisation uses the exact source-locked INE age-18 series;
the older 15-24 divided-by-ten proxy is retained only as a secondary sensitivity.

The paper does not claim that a 1997-2026 programme-level panel has been reconstructed.
That historical extension is future work and is no longer a release gate for the
current Study A result. The current evidence supports the narrower conclusion that
absolute first-phase STEM placements do not show a sustained decline over the
source-locked 2017-2026 window, while placement share is slightly lower and component
paths differ materially.
