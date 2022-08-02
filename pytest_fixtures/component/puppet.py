# Puppet Environment fixtures
import pytest

from robottelo.config import settings
from robottelo.constants import ENVIRONMENT
from robottelo.helpers import InstallerCommand


common_opts = {
    'foreman-proxy-puppetca': 'true',
    'foreman-proxy-content-puppet': 'true',
    'foreman-proxy-puppet': 'true',
    'puppet-server': 'true',
    'puppet-server-foreman-ssl-ca': '/etc/pki/katello/puppet/puppet_client_ca.crt',
    'puppet-server-foreman-ssl-cert': '/etc/pki/katello/puppet/puppet_client.crt',
    'puppet-server-foreman-ssl-key': '/etc/pki/katello/puppet/puppet_client.key',
    # Options for puppetbootstrap test
    'foreman-proxy-templates': 'true',
    'foreman-proxy-http': 'true',
}

enable_satellite_cmd = InstallerCommand(
    installer_args=[
        'enable-foreman-plugin-puppet',
        'enable-foreman-cli-puppet',
        'enable-puppet',
    ],
    installer_opts=common_opts,
)

enable_capsule_cmd = InstallerCommand(
    installer_args=[
        'enable-puppet',
    ],
    installer_opts=common_opts,
)


@pytest.fixture(scope='session')
def session_puppet_enabled_sat(session_satellite_host):
    """Satellite with enabled puppet plugin"""
    result = session_satellite_host.execute(enable_satellite_cmd.get_command(), timeout='20m')
    assert result.status == 0
    session_satellite_host.execute('hammer -r')  # workaround for BZ#2039696
    yield session_satellite_host


@pytest.fixture(scope='module')
def module_puppet_org(session_puppet_enabled_sat):
    yield session_puppet_enabled_sat.api.Organization().create()


@pytest.fixture(scope='module')
def module_puppet_loc(session_puppet_enabled_sat):
    yield session_puppet_enabled_sat.api.Location().create()


@pytest.fixture(scope='module')
def module_puppet_domain(session_puppet_enabled_sat, module_puppet_loc, module_puppet_org):
    yield session_puppet_enabled_sat.api.Domain(
        location=[module_puppet_loc], organization=[module_puppet_org]
    ).create()


@pytest.fixture(scope='session')
def default_puppet_environment(module_puppet_org, session_puppet_enabled_sat):
    environments = session_puppet_enabled_sat.api.Environment().search(
        query=dict(search=f'organization_id={module_puppet_org.id}')
    )
    if environments:
        return environments[0].read()


@pytest.fixture(scope='module')
def module_puppet_environment(module_puppet_org, module_puppet_loc, session_puppet_enabled_sat):
    environment = session_puppet_enabled_sat.api.Environment(
        organization=[module_puppet_org], location=[module_puppet_loc]
    ).create()
    return session_puppet_enabled_sat.api.Environment(id=environment.id).read()


@pytest.mark.skipif((not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url')
@pytest.fixture(scope='module')
def module_import_puppet_module(session_puppet_enabled_sat):
    """Returns custom puppet environment name that contains imported puppet module
    and puppet class name."""
    puppet_class = 'generic_1'
    return {
        'puppet_class': puppet_class,
        'env': session_puppet_enabled_sat.create_custom_environment(repo=puppet_class),
    }


@pytest.fixture(scope='module')
def module_env_search(
    module_puppet_org, module_puppet_loc, module_import_puppet_module, session_puppet_enabled_sat
):
    """Search for puppet environment created from module_import_puppet_module fixture.

    Returns the puppet environment with updated organization and location.
    """
    env = (
        session_puppet_enabled_sat.api.Environment()
        .search(query={'search': f'name={module_import_puppet_module["env"]}'})[0]
        .read()
    )
    env.location = [module_puppet_loc]
    env.organization = [module_puppet_org]
    env.update(['location', 'organization'])
    return env


@pytest.fixture(scope='module')
def module_puppet_classes(
    module_env_search, module_import_puppet_module, session_puppet_enabled_sat
):
    """Returns puppet class based on following criteria:
    Puppet environment from module_env_search and puppet class name.
    """
    return session_puppet_enabled_sat.api.PuppetClass().search(
        query={
            'search': f'name ~ {module_import_puppet_module["puppet_class"]} '
            f'and environment = {module_env_search.name}'
        }
    )


@pytest.fixture(scope='session', params=[True, False], ids=["puppet_enabled", "puppet_disabled"])
def parametrized_puppet_sat(request, session_target_sat, session_puppet_enabled_sat):
    if request.param:
        sat = session_puppet_enabled_sat
    else:
        sat = session_target_sat
    return {'sat': sat, 'enabled': request.param}


@pytest.fixture(scope="session")
def session_puppet_enabled_proxy(session_puppet_enabled_sat):
    """Use the default installation puppet smart proxy"""
    return (
        session_puppet_enabled_sat.api.SmartProxy()
        .search(query={'search': f'url = {session_puppet_enabled_sat.url}:9090'})[0]
        .read()
    )


@pytest.fixture(scope='session')
def session_puppet_default_os(session_puppet_enabled_sat):
    """Default OS on the puppet-enabled Satellite"""
    search_string = 'name="RedHat" AND (major="6" OR major="7" OR major="8")'
    return (
        session_puppet_enabled_sat.api.OperatingSystem()
        .search(query={'search': search_string})[0]
        .read()
    )


@pytest.fixture(scope='module')
def module_puppet_published_cv(session_puppet_enabled_sat, module_puppet_org):
    content_view = session_puppet_enabled_sat.api.ContentView(
        organization=module_puppet_org
    ).create()
    content_view.publish()
    return content_view.read()


@pytest.fixture(scope='module')
def module_puppet_lce_library(session_puppet_enabled_sat, module_puppet_org):
    """Returns the Library lifecycle environment from chosen organization"""
    return (
        session_puppet_enabled_sat.api.LifecycleEnvironment()
        .search(query={'search': f'name={ENVIRONMENT} and organization_id={module_puppet_org.id}'})[
            0
        ]
        .read()
    )


@pytest.fixture(scope='module')
def module_puppet_user(session_puppet_enabled_sat, module_puppet_org, module_puppet_loc):
    return session_puppet_enabled_sat.api.User(
        organization=[module_puppet_org], location=[module_puppet_loc]
    ).create()
