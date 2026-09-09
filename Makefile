.PHONY: test lint typecheck quality study-a-recent study-a-medium-run study-a-age18 \
	study-a-demographic study-a-public study-b-pilot study-b-multi-course \
	study-b-regionality study-b-ranking-coverage study-b-public empirical-public paper \
	validate-release clean

test:
	pytest

lint:
	ruff check .

typecheck:
	mypy src

quality: lint typecheck test

study-a-recent:
	python scripts/build_study_a_recent.py

study-a-medium-run:
	python scripts/build_study_a_medium_run.py

study-a-age18:
	python scripts/build_study_a_age18.py

study-a-demographic:
	python scripts/build_study_a_demographic.py

study-a-public: study-a-recent study-a-medium-run study-a-age18 study-a-demographic

study-b-pilot:
	python scripts/build_study_b_course9119_pilot.py

study-b-multi-course:
	python scripts/build_study_b_multi_course.py

study-b-regionality:
	python scripts/build_study_b_regionality.py

study-b-ranking-coverage:
	python -m scripts.build_study_b_ranking_coverage

study-b-public: study-b-pilot study-b-multi-course study-b-regionality study-b-ranking-coverage

empirical-public: study-a-public study-b-public

paper: empirical-public
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex

validate-release:
	python scripts/validate_release_candidate.py

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov
	rm -f paper/*.aux paper/*.log paper/*.out paper/*.pdf
