# Variables -------------------------------------------------------------------

ROBOTTELO_TESTS_PATH=tests/robottelo/
FOREMAN_TESTS_PATH=tests/foreman/
FOREMAN_API_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), api)
FOREMAN_CLI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), cli)
FOREMAN_UI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), ui)
FOREMAN_SMOKE_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), smoke)

# Commands --------------------------------------------------------------------

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  docs                  to make documentation in the default format"
	@echo "  docs-clean            to remove docs and doc build artifacts"
	@echo "  test-docstrings       to check whether docstrings are good quality"
	@echo "  test-robottelo        to run internal robottelo tests"
	@echo "  test-foreman-api      to test a Foreman deployment API"
	@echo "  test-foreman-cli      to test a Foreman deployment CLI"
	@echo "  test-foreman-ui       to test a Foreman deployment UI"
	@echo "  test-foreman-ui-xvfb  to test a Foreman deployment UI using xvfb-run"
	@echo "  test-foreman-smoke    to perform a generic smoke test"
	@echo "  graph-entities        to graph entity relationships"
	@echo "  lint                  to run pylint on the entire codebase"

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

test-foreman-ui-xvfb:
	xvfb-run nosetests -c robottelo.properties $(FOREMAN_UI_TESTS_PATH)

test-foreman-smoke:
	nosetests -c robottelo.properties $(FOREMAN_SMOKE_TESTS_PATH)

graph-entities:
	scripts/graph_entities.py | dot -Tsvg -o entities.svg

lint:
	scripts/lint.py

# Special Targets -------------------------------------------------------------

.PHONY: help docs docs-clean test-docstrings test-robottelo \
        test-foreman-api test-foreman-cli test-foreman-ui \
        test-foreman-ui-xvfb test-foreman-smoke graph-entities lint
