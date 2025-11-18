include .make/base.mk

PYTHON_LINT_TARGET = src/ tests/

isort:
	uv run isort --profile black ${PYTHON_LINT_TARGET}

black:
	uv run black ${PYTHON_LINT_TARGET}

python-format: isort black


isorted: 
	uv run isort --check-only --profile black $(PYTHON_LINT_TARGET)

blacked:
	uv run black --check $(PYTHON_LINT_TARGET)

flake8:
	uv run flake8 $(PYTHON_LINT_TARGET)

pylint:
	uv run pylint --output-format=parseable,parseable:build/code_analysis.stdout,pylint_junit.JUnitReporter:build/reports/linting-python.xml $(PYTHON_LINT_TARGET)

python-lint: isorted blacked flake8 pylint

python-test:
	uv run pytest tests/
