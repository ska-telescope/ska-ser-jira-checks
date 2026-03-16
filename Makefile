include .make/base.mk
include .make-uv/make/python-uv.mk

# Load secrets if they exist
-include .env
export

PYTHON_LINT_TARGET = tests
