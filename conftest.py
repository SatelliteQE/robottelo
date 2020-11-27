"""Global Configurations for py.test runner"""

pytest_plugins = [
    # Plugins
    "pytest_plugins.rerun_rp.rerun_rp",
    "pytest_plugins.markers",
    "pytest_plugins.issue_handlers",
    "pytest_plugins.manual_skipped",
    # Fixtures
    "pytest_fixtures.api_fixtures",
    "pytest_fixtures.xdist",
    "pytest_fixtures.broker",
    # Component Fixtures
    "pytest_fixtures.satellite_auth",
    "pytest_fixtures.sys_fixtures",
    "pytest_fixtures.templatesync_fixtures",
    "pytest_fixtures.ansible_fixtures",
    "pytest_fixtures.oscap_fixtures",
    "pytest_fixtures.smartproxy_fixtures",
    "pytest_fixtures.user_fixtures",
]
