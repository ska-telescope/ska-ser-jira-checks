include .make/base.mk
include .make-uv/make/python-uv.mk

-include .env
export

PYTHON_LINT_TARGET = src/ tests/

report:
	uv run ska-ser-jira-checks --output-dir reports

.PHONY: report
