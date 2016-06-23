# Variables -------------------------------------------------------------------

FOREMAN_API_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), api)
FOREMAN_CLI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), cli)
FOREMAN_RHAI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), rhai)
FOREMAN_RHCI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), rhci)
FOREMAN_SMOKE_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), smoke)
FOREMAN_TIERS_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), {api,cli,ui})
FOREMAN_TESTS_PATH=tests/foreman/
FOREMAN_UI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), ui)
PYTEST=python -m cProfile -o $@.pstats $$(which py.test)
PYTEST_OPTS=-v --junit-xml=foreman-results.xml -m 'not stubbed'
PYTEST_XDIST_NUMPROCESSES=auto
PYTEST_XDIST_OPTS=$(PYTEST_OPTS) -n $(PYTEST_XDIST_NUMPROCESSES) --boxed
ROBOTTELO_TESTS_PATH=tests/robottelo/
TESTIMONY_TOKENS="assert, bz, caseautomation, casecomponent, caseimportance, caselevel, caseposneg, id, requirement, setup, subtype1, steps, testtype, upstream"
TESTIMONY_MINIMUM_TOKENS="id, requirement, caseautomation, caselevel, casecomponent, testtype, caseimportance, upstream"
TESTIMONY_OPTIONS=--tokens=$(TESTIMONY_TOKENS) --minimum-tokens=$(TESTIMONY_MINIMUM_TOKENS)

# Commands --------------------------------------------------------------------

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  docs                       to make documentation in the default format"
	@echo "  docs-clean                 to remove docs and doc build artifacts"
	@echo "  test-docstrings            to check whether docstrings are good quality"
	@echo "  test-robottelo             to run internal robottelo tests"
	@echo "  test-robottelo-coverage    to run internal robottelo tests with coverage report."
	@echo "                             Requires pytest-cov"
	@echo "  test-foreman-tier1         to run Foreman deployment tier1 tests"
	@echo "  test-foreman-tier2         to run Foreman deployment tier2 tests"
	@echo "  test-foreman-tier3         to run Foreman deployment tier3 tests"
	@echo "  test-foreman-tier4         to run Foreman deployment tier4 tests"
	@echo "  test-foreman-api           to test a Foreman deployment API"
	@echo "  test-foreman-api-threaded  to do the above with threading."
	@echo "                             Requires pytest-xdist"
	@echo "  test-foreman-cli           to test a Foreman deployment CLI"
	@echo "  test-foreman-cli-threaded  to do the above with threading."
	@echo "                             Requires pytest-xdist"
	@echo "  test-foreman-rhai          to test Red Hat Insights plugin"
	@echo "  test-foreman-rhci          to test a Foreman deployment w/RHCI plugin"
	@echo "  test-foreman-ui            to test a Foreman deployment UI"
	@echo "  test-foreman-ui-xvfb       to test a Foreman deployment UI using xvfb-run"
	@echo "  test-foreman-smoke         to perform a generic smoke test"
	@echo "  graph-entities             to graph entity relationships"
	@echo "  lint                       to run pylint on the entire codebase"
	@echo "  logs-join                  to join xdist log files into one"
	@echo "  logs-clean                 to delete all xdist log files in the root"
	@echo "  pyc-clean                  to delete all temporary artifacts"

docs:
	@cd docs; $(MAKE) html

docs-clean:
	@cd docs; $(MAKE) clean

test-docstrings:
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/api
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/cli
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/rhci
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/ui
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/rhai

test-robottelo:
	$$(which py.test) -s  $(ROBOTTELO_TESTS_PATH)

test-robottelo-coverage:
	$$(which py.test) --cov --cov-config=.coveragerc tests/robottelo

test-foreman-api:
	$(PYTEST) $(PYTEST_OPTS) $(FOREMAN_API_TESTS_PATH)

test-foreman-api-threaded:
	$(PYTEST) $(PYTEST_XDIST_OPTS) $(FOREMAN_API_TESTS_PATH)

test-foreman-cli:
	$(PYTEST) $(PYTEST_OPTS) $(FOREMAN_CLI_TESTS_PATH)

test-foreman-cli-threaded:
	$(PYTEST) $(PYTEST_XDIST_OPTS) $(FOREMAN_CLI_TESTS_PATH)

test-foreman-rhai:
	$(PYTEST) $(PYTEST_OPTS) $(FOREMAN_RHAI_TESTS_PATH)

test-foreman-rhci:
	$(PYTEST) $(PYTEST_OPTS) $(FOREMAN_RHCI_TESTS_PATH)

test-foreman-ui:
	$(PYTEST) $(PYTEST_OPTS) $(FOREMAN_UI_TESTS_PATH)

test-foreman-ui-xvfb:
	xvfb-run py.test $(PYTEST_OPTS) $(FOREMAN_UI_TESTS_PATH)

test-foreman-smoke:
	$(PYTEST) $(PYTEST_OPTS) $(FOREMAN_SMOKE_TESTS_PATH)

test-foreman-tier1:
	$(PYTEST) $(PYTEST_XDIST_OPTS) -m 'not stubbed and tier1' $(FOREMAN_TIERS_TESTS_PATH)

test-foreman-tier2:
	$(PYTEST) $(PYTEST_XDIST_OPTS) -m 'not stubbed and tier2' $(FOREMAN_TIERS_TESTS_PATH)

test-foreman-tier3:
	$(PYTEST) $(PYTEST_XDIST_OPTS) -m 'not stubbed and tier3' $(FOREMAN_TIERS_TESTS_PATH)

test-foreman-tier4:
	$(PYTEST) $(PYTEST_XDIST_OPTS) -m 'not stubbed and tier4' $(join $(FOREMAN_TESTS_PATH), longrun)

graph-entities:
	scripts/graph_entities.py | dot -Tsvg -o entities.svg

lint:
	scripts/lint.py

pyc-clean: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

logs-join:
	-cat robottelo_gw*.log > robottelo_master.log

logs-clean:
	-rm -f robottelo_gw*.log

# Special Targets -------------------------------------------------------------

.PHONY: help docs docs-clean test-docstrings test-robottelo \
        test-robottelo-coverage test-foreman-api test-foreman-cli \
        test-foreman-rhai test-foreman-rhci test-foreman-tier1 \
        test-foreman-tier2 test-foreman-tier3 test-foreman-tier4 \
        test-foreman-ui test-foreman-ui-xvfb test-foreman-smoke \
        graph-entities lint logs-join logs-clean pyc-clean
