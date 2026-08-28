.PHONY: test lint typecheck quality study-a-recent study-a-medium-run paper clean

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

paper: study-a-recent study-a-medium-run
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov
	rm -f paper/*.aux paper/*.log paper/*.out paper/*.pdf
