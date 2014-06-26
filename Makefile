# Variables -------------------------------------------------------------------

ROBOTTELO_TESTS_PATH=tests/robottelo/
FOREMAN_TESTS_PATH=tests/foreman/
FOREMAN_API_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), api)
FOREMAN_CLI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), cli)
FOREMAN_UI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), ui)

# Commands --------------------------------------------------------------------

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  docs             to make documentation in default format"
	@echo "  docs-clean       to remove docs and doc build artifacts"
	@echo "  test-docstrings  to check whether docstrings are good quality"
	@echo "  test-robottelo   to run internal robottelo tests"
	@echo "  test-foreman-api to test a Satellite deployment API"
	@echo "  test-foreman-cli to test a Satellite deployment CLI"
	@echo "  test-foreman-ui  to test a Satellite deployment UI"

docs:
	@cd docs; $(MAKE) html

docs-clean:
	@cd docs; $(MAKE) clean

test-docstrings:
	testimony validate_docstring tests/foreman/api
	testimony validate_docstring tests/foreman/cli
	testimony validate_docstring tests/foreman/ui

test-robottelo:
	nosetests -c robottelo.properties $(ROBOTTELO_TESTS_PATH)

test-foreman-api:
	nosetests -c robottelo.properties $(FOREMAN_API_TESTS_PATH)

test-foreman-cli:
	nosetests -c robottelo.properties $(FOREMAN_CLI_TESTS_PATH)

test-foreman-ui:
	nosetests -c robottelo.properties $(FOREMAN_UI_TESTS_PATH)

# Special Targets -------------------------------------------------------------

.PHONY: help docs docs-clean test-docstrings test-robottelo \
        test-foreman-api test-foreman-cli test-foreman-ui
