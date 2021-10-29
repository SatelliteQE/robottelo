"""Global Configurations for py.test runner"""

pytest_plugins = [
    # Plugins
    'pytest_plugins.disable_rp_params',
    'pytest_plugins.infra_dependent_markers',
    'pytest_plugins.issue_handlers',
    'pytest_plugins.logging_hooks',
    'pytest_plugins.manual_skipped',
    'pytest_plugins.marker_deselection',
    'pytest_plugins.markers',
    'pytest_plugins.testimony_markers',
    'pytest_plugins.settings_skip',
    'pytest_plugins.rerun_rp.rerun_rp',
    # Fixtures
    'pytest_fixtures.api_fixtures',
    'pytest_fixtures.broker',
    'pytest_fixtures.content_hosts',
    'pytest_fixtures.reporting_fixtures',
    'pytest_fixtures.xdist',
    # Component Fixtures
    'pytest_fixtures.ansible_fixtures',
    'pytest_fixtures.oscap_fixtures',
    'pytest_fixtures.rh_cloud',
    'pytest_fixtures.satellite_auth',
    'pytest_fixtures.sys_fixtures',
    'pytest_fixtures.smartproxy_fixtures',
    'pytest_fixtures.templatesync_fixtures',
    'pytest_fixtures.user_fixtures',
    'pytest_fixtures.upgrade_fixtures',
]
