"""Global Configurations for py.test runner"""

pytest_plugins = [
    # Plugins
    "pytest_plugins.uncollector",
    # Fixtures
    "pytest_fixtures.api_fixtures",
    # Component Fixtures
    "pytest_fixtures.satellite_auth",
]
