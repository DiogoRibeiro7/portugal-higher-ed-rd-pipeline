# Release validation — v0.3.4

Date: 2026-09-10

## Release status

**Tag-ready, pending publication.**

The scientific boundary for v0.3.4 is frozen, and release metadata are aligned across
`pyproject.toml`, runtime `pt_he_pipeline.__version__`, `CITATION.cff`, and
`config/study.yml`.

GitHub Actions has successfully executed the full hosted release gate on the exact final
release-candidate commit, including lock validation, dependency installation, Ruff, strict
mypy, pytest, all public Study A and Study B rebuilds, TeX installation, and the two-pass
manuscript compile. The v0.3.4 tag and GitHub release may therefore be created from the exact
validated release tree once this status-only update itself has passed the same hosted gate.

## Scientific boundary

### Study A

The current empirical Study A phase is complete for the source-locked broad-area first-phase
window covering 2017, 2018 and 2020-2026. The comparable 2019 field-composition table remains
unobserved and is not imputed, interpolated or reconstructed.

The registered primary STEM definition remains ISCED-F/CITE-F groups 05, 06 and 07, reported
componentwise before aggregation. Between the observed endpoints 2017 and 2026:

- all-STEM placements change by **+9.0%**;
- the exact age-18-normalised placement rate changes by **+9.1%**;
- the all-STEM share of national first-phase placements changes by **-0.64 percentage points**;
- group 05 declines, while groups 06 and 07 increase.

The available 2017-2026 evidence therefore does not support describing absolute first-phase
STEM placements as one sustained decline. This remains a descriptive administrative-data
result, not a causal or sampling-inference claim.

The preferred demographic denominator is the source-locked INE resident population aged
exactly 18. The older 15-24 divided-by-ten cohort proxy is retained only as a weaker secondary
sensitivity.

### Study B

Study B remains secondary cross-domain calibration rather than primary evidence for the STEM
placement claim. The current manuscript uses the registered five-programme 2018-2020 panel,
recent regionality evidence, and provider-specific ranking analyses under the previously frozen
measurement and interpretation rules.

A separately registered 2021 five-programme extension is retained in the repository as an
additional robustness layer. It does not silently change the manuscript's frozen 2018-2020
Study B estimand or the v0.3.4 headline Study A conclusion.

Ranking results remain predictive and associational. The attenuation of ranking information
after conditioning on contemporaneous demand is not interpreted as causal mediation.

### Study C

Study C remains a separate downstream R&D-pipeline research track. No downstream research
capacity conclusion is inferred from admissions alone, and Study C is not a blocker for the
current Study A release.

## Reproducibility boundary

All empirical layers that can be rebuilt from committed or otherwise redistributable inputs are
exposed through:

```bash
make empirical-public
```

This rebuilds:

- Study A recent baseline;
- Study A medium-run layer;
- exact age-18 normalisation;
- broad-cohort demographic sensitivity;
- historical Study B matched-course pilot;
- registered five-programme Study B panel;
- public Study B regionality outputs;
- provider/year ranking coverage from committed audit inputs.

The provider-specific ranking model itself is intentionally excluded from the public rebuild.
Its runner requires the non-redistributed private historical ranking panel and validates that
panel against the frozen SHA-256 contract before fitting. Exact ranking-model reproduction
therefore requires authorised access to that private panel; the repository does not weaken this
provenance boundary for release convenience.

The manuscript can be rebuilt after the public empirical layers with:

```bash
make paper
```

The `paper` target recompiles the committed manuscript after rebuilding all public empirical
layers. It does not claim to regenerate the private-input ranking model.

## Local release-candidate validation

An exact checkout can also be validated locally with:

```bash
make validate-release
```

The validator refuses to start from a dirty checkout. It records the exact Git commit and then
runs the release gates in sequence:

1. Poetry lock validation;
2. dependency installation;
3. Ruff;
4. strict mypy over `src`;
5. pytest with package coverage;
6. every publicly reproducible Study A and Study B builder;
7. two `pdflatex` manuscript passes;
8. a final Git working-tree check so rebuild drift fails validation.

Command logs, environment metadata and a machine-readable summary are written under
`validation/results/<commit>/`. These files are local evidence for that exact checkout.
A **LOCAL PASS is not equivalent to tag-ready** and does not replace the hosted GitHub Actions
gate.

## Automated release gate

GitHub Actions is configured to require, on a provisioned runner:

1. lock-file validation;
2. dependency installation;
3. full-repository Ruff checks;
4. strict mypy checks over `src`;
5. the pytest suite with package coverage;
6. rebuild of all public Study A release layers;
7. rebuild of all public Study B release layers;
8. TeX installation with scalable Computer Modern fonts;
9. two-pass manuscript compilation with a non-empty PDF output.

The version-consistency regression additionally requires agreement among:

- `pyproject.toml`;
- runtime `pt_he_pipeline.__version__`;
- `CITATION.cff`;
- `config/study.yml`.

## Tagging gate

Create the v0.3.4 tag and GitHub release only after all of the following are true on the exact
commit to be tagged:

- GitHub Actions provisions a runner and executes the workflow;
- every required CI step completes successfully;
- the public empirical rebuilds complete without modifying the scientific boundary;
- the manuscript compiles from the release tree;
- release metadata still report exactly `0.3.4`;
- no new scientific result, parser, sensitivity or source-ingestion change has entered after the
  consolidation freeze without a demonstrated release need.

Those conditions have been satisfied for the current v0.3.4 release candidate. After this
status-only update passes the same hosted gate, its exact merge commit is the final tag target.
