"""Global Configurations for py.test runner"""

pytest_plugins = [
    # Plugins
    'pytest_plugins.rerun_rp.rerun_rp',
    'pytest_plugins.infra_dependent_markers',
    'pytest_plugins.marker_deselection',
    'pytest_plugins.markers',
    'pytest_plugins.issue_handlers',
    'pytest_plugins.testimony_markers',
    'pytest_plugins.manual_skipped',
    'pytest_plugins.disable_rp_params',
    'pytest_plugins.settings_skip',
    # Fixtures
    'pytest_fixtures.api_fixtures',
    'pytest_fixtures.broker',
    'pytest_fixtures.xdist',
    'pytest_fixtures.reporting_fixtures',
    # Component Fixtures
    'pytest_fixtures.ansible_fixtures',
    'pytest_fixtures.oscap_fixtures',
    'pytest_fixtures.rh_cloud',
    'pytest_fixtures.satellite_auth',
    'pytest_fixtures.certificate',
    'pytest_fixtures.sys_fixtures',
    'pytest_fixtures.smartproxy_fixtures',
    'pytest_fixtures.templatesync_fixtures',
    'pytest_fixtures.user_fixtures',
    'pytest_fixtures.upgrade_fixtures',
]
