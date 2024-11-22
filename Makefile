include .make/base.mk
include .make/python.mk

PYTHON_LINE_LENGTH = 88
PYTHON_LINT_TARGET = tests
PYTHON_VARS_AFTER_PYTEST = -ra -v
