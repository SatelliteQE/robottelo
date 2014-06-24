# Paths
ROBOTTELO_TESTS_PATH=tests/robottelo/
FOREMAN_TESTS_PATH=tests/foreman/
FOREMAN_API_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), api)
FOREMAN_CLI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), cli)
FOREMAN_UI_TESTS_PATH=$(join $(FOREMAN_TESTS_PATH), ui)


docs:
	@cd docs; $(MAKE) html

docs-clean:
	@cd docs; $(MAKE) clean

test-robottelo:
	nosetests -c robottelo.properties $(ROBOTTELO_TESTS_PATH)

test-foreman-api:
	nosetests -c robottelo.properties $(FOREMAN_API_TESTS_PATH)

test-foreman-cli:
	nosetests -c robottelo.properties $(FOREMAN_CLI_TESTS_PATH)

test-foreman-ui:
	nosetests -c robottelo.properties $(FOREMAN_UI_TESTS_PATH)

.PHONY: docs docs-clean test test-foreman-api test-foreman-cli test-foreman-ui
