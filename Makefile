# Variables -------------------------------------------------------------------

FOREMAN_API_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), api)
FOREMAN_CLI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), cli)
FOREMAN_LONGRUN_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), longrun)
FOREMAN_RHAI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), rhai)
FOREMAN_RHCI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), rhci)
FOREMAN_SMOKE_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), smoke)
FOREMAN_TESTS_PATH=tests/foreman/
FOREMAN_UI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), ui)
NOSETESTS=python -m cProfile -o $@.pstats $$(which nosetests)
NOSETESTS_OPTS=--logging-filter=nailgun,robottelo --with-xunit\
			   --xunit-file=foreman-results.xml
ROBOTTELO_TESTS_PATH=tests/robottelo/

# Commands --------------------------------------------------------------------

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  docs                  to make documentation in the default format"
	@echo "  docs-clean            to remove docs and doc build artifacts"
	@echo "  test-docstrings       to check whether docstrings are good quality"
	@echo "  test-robottelo        to run internal robottelo tests"
	@echo "  test-foreman-api      to test a Foreman deployment API"
	@echo "  test-foreman-api-threaded  to do the above with threading"
	@echo "  test-foreman-cli      to test a Foreman deployment CLI"
	@echo "  test-foreman-cli-threaded  to do the above with threading"
	@echo "  test-foreman-rhai	   to test Red Hat Access Insights plugin"
	@echo "  test-foreman-rhci     to test a Foreman deployment w/RHCI plugin"
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
	testimony validate_docstring tests/foreman/rhci
	testimony validate_docstring tests/foreman/ui
	testimony validate_docstring tests/foreman/rhai

test-robottelo:
	$$(which nosetests) $(ROBOTTELO_TESTS_PATH)

test-foreman-api:
	$(NOSETESTS) $(NOSETESTS_OPTS) $(FOREMAN_API_TESTS_PATH)

test-foreman-api-threaded:
	$(NOSETESTS) $(NOSETESTS_OPTS) $(FOREMAN_API_TESTS_PATH)\
	    --processes=-1 --process-timeout=300

test-foreman-cli:
	$(NOSETESTS) $(NOSETESTS_OPTS) $(FOREMAN_CLI_TESTS_PATH)

test-foreman-cli-threaded:
	$(NOSETESTS) $(NOSETESTS_OPTS) $(FOREMAN_CLI_TESTS_PATH)\
	    --processes=-1 --process-timeout=300

test-foreman-longrun:
	$(NOSETESTS) $(NOSETESTS_OPTS) $(FOREMAN_LONGRUN_TESTS_PATH)

test-foreman-rhai:
	$(NOSETESTS) $(NOSETESTS_OPTS) $(FOREMAN_RHAI_TESTS_PATH)

test-foreman-rhci:
	$(NOSETESTS) $(NOSETESTS_OPTS) $(FOREMAN_RHCI_TESTS_PATH)

test-foreman-ui:
	$(NOSETESTS) $(NOSETESTS_OPTS) $(FOREMAN_UI_TESTS_PATH)

test-foreman-ui-xvfb:
	xvfb-run nosetests $(NOSETESTS_OPTS) $(FOREMAN_UI_TESTS_PATH)

test-foreman-smoke:
	$(NOSETESTS) $(NOSETESTS_OPTS) $(FOREMAN_SMOKE_TESTS_PATH)

graph-entities:
	scripts/graph_entities.py | dot -Tsvg -o entities.svg

lint:
	scripts/lint.py

# Special Targets -------------------------------------------------------------

.PHONY: help docs docs-clean test-docstrings test-robottelo \
        test-foreman-api test-foreman-cli test-foreman-rhai test-foreman-rhci \
        test-foreman-ui test-foreman-ui-xvfb test-foreman-smoke \
        graph-entities lint
