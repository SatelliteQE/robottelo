# Variables -------------------------------------------------------------------

FOREMAN_API_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), api)
FOREMAN_CLI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), cli)
FOREMAN_RHAI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), rhai)
FOREMAN_VIRTWHO_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), virtwho)
FOREMAN_ENDTOEND_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), endtoend)
FOREMAN_TIERS_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), {api,cli,ui})
FOREMAN_TESTS_PATH=tests/foreman/
FOREMAN_UI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), ui)
PYTEST=python -m cProfile -o $@.pstats $$(which py.test)
PYTEST_OPTS=-v --junit-xml=foreman-results.xml -m 'not stubbed'
PYTEST_XDIST_NUMPROCESSES=auto
PYTEST_XDIST_OPTS=$(PYTEST_OPTS) -n $(PYTEST_XDIST_NUMPROCESSES)
ROBOTTELO_TESTS_PATH=tests/robottelo/
TESTIMONY_OPTIONS=--config testimony.yaml

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
	@echo "  test-foreman-sys           to run Foreman deployment sys tests"
	@echo "  test-foreman-api           to test a Foreman deployment API"
	@echo "  test-foreman-api-threaded  to do the above with threading."
	@echo "                             Requires pytest-xdist"
	@echo "  test-foreman-cli           to test a Foreman deployment CLI"
	@echo "  test-foreman-cli-threaded  to do the above with threading."
	@echo "                             Requires pytest-xdist"
	@echo "  test-foreman-rhai          to test Red Hat Insights plugin"
	@echo "  test-foreman-ui            to test a Foreman deployment UI"
	@echo "  test-foreman-ui-xvfb       to test a Foreman deployment UI using xvfb-run"
	@echo "  test-foreman-virtwho       to test a Foreman deployment Virtwho Configure plugin"
	@echo "  test-foreman-upgrade       to run Foreman deployment post-upgrade tests"
	@echo "  test-foreman-endtoend      to perform a generic end-to-end test"
	@echo "  graph-entities             to graph entity relationships"
	@echo "  logs-join                  to join xdist log files into one"
	@echo "  logs-clean                 to delete all xdist log files in the root"
	@echo "  pyc-clean                  to delete all temporary artifacts"
	@echo "  uuid-check                 to check for duplicated or empty :id: in testimony docstring tags"
	@echo "  uuid-fix                   to fix all duplicated or empty :id: in testimony docstring tags"
	@echo "  token-prefix-editor        to fix all tokens prefix and ensure :<token>: format"
	@echo "  can-i-push                 to check if local changes are suitable to push"
	@echo "  clean-shared               to clean shared functions storage data files"
	@echo "  clean-cache                to clean pytest cache files"
	@echo "  clean-all                  to clean cache, pyc, logs and docs"

docs:
	$(info "Copying broker_config.yaml to avoid warnings")
	@cp ./broker_settings.yaml docs/; $(MAKE) -C docs html

docs-clean:
	$(info "Cleaning docs...")
	$(MAKE) -C docs clean

test-docstrings: uuid-check
	$(info "Checking for errors in docstrings and testimony tags...")
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/api
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/cli
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/endtoend
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/installer
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/longrun
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/sys
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/ui
	testimony $(TESTIMONY_OPTIONS) validate tests/foreman/virtwho

test-robottelo:
	$(info "Running robottelo framework unit tests...")
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

test-foreman-ui:
	$(PYTEST) $(PYTEST_OPTS) $(FOREMAN_UI_TESTS_PATH)

test-foreman-ui-xvfb:
	xvfb-run py.test $(PYTEST_OPTS) $(FOREMAN_UI_TESTS_PATH)

test-foreman-virtwho:
	$(PYTEST) $(PYTEST_OPTS) $(FOREMAN_VIRTWHO_TESTS_PATH)

test-foreman-endtoend:
	$(PYTEST) $(PYTEST_OPTS) $(FOREMAN_ENDTOEND_TESTS_PATH)

test-foreman-tier1:
	$(PYTEST) $(PYTEST_XDIST_OPTS) -m 'not stubbed and tier1' $(FOREMAN_TIERS_TESTS_PATH)

test-foreman-tier2:
	$(PYTEST) $(PYTEST_XDIST_OPTS) -m 'not stubbed and tier2' $(FOREMAN_TIERS_TESTS_PATH)

test-foreman-tier3:
	$(PYTEST) $(PYTEST_XDIST_OPTS) -m 'not stubbed and tier3' $(FOREMAN_TIERS_TESTS_PATH)

test-foreman-tier4:
	$(PYTEST) $(PYTEST_XDIST_OPTS) -m 'not stubbed and tier4' $(join $(FOREMAN_TESTS_PATH), longrun)

test-foreman-sys:
	$(PYTEST) $(PYTEST_OPTS) -m 'not stubbed and destructive' $(FOREMAN_TESTS_PATH)

test-foreman-upgrade:
	$(PYTEST) $(PYTEST_XDIST_OPTS) -m 'not stubbed and upgrade' $(FOREMAN_TIERS_TESTS_PATH)

graph-entities:
	scripts/graph_entities.py | dot -Tsvg -o entities.svg

pyc-clean: ## remove Python file artifacts
	$(info "Removing unused Python compiled files, caches and ~ backups...")
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

logs-join:
	$(info "Joining worker logs in to one master file...")
	-cat robottelo_gw*.log > robottelo_master.log

logs-clean:
	$(info "Removing pytest worker logs...")
	-rm -f robottelo_gw*.log

clean-shared:
	$(info "Removing shared_functions temp folders...")
	-rm -rf /tmp/robottelo/shared_functions
	-rm -rf /var/tmp/robottelo/shared_functions

uuid-check:  ## list duplicated or empty uuids
	$(info "Checking for empty or duplicated @id: in docstrings...")
	@scripts/fix_uuids.sh --check

uuid-fix:
	@scripts/fix_uuids.sh

token-prefix-editor:
	@scripts/token_editor.py

can-i-push: uuid-check test-docstrings test-robottelo
	$(info "!!! Congratulations your changes are good to fly, make a great PR! ${USER}++ !!!")

clean-cache:
	$(info "Cleaning the .cache directory...")
	rm -rf .cache

clean-all: docs-clean logs-clean pyc-clean clean-cache clean-shared

customer-scenario-check:
	$(info "Checking the customer scenario status of associated BZs")
	@scripts/customer_scenarios.py --paths $(paths)

# Special Targets -------------------------------------------------------------

.PHONY: help docs docs-clean test-docstrings test-robottelo \
        test-robottelo-coverage test-foreman-api test-foreman-cli \
        test-foreman-rhai test-foreman-tier1 \
        test-foreman-tier2 test-foreman-tier3 test-foreman-tier4 \
        test-foreman-sys test-foreman-ui test-foreman-ui-xvfb \
        test-foreman-virtwho test-foreman-ui \
        test-foreman-endtoend graph-entities logs-join \
        logs-clean pyc-clean uuid-check uuid-fix token-prefix-editor \
        can-i-push clean-cache clean-all \
        clean-shared
