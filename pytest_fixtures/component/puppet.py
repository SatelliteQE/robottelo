# Puppet Environment fixtures
import pytest

from robottelo.config import settings
from robottelo.helpers import InstallerCommand

enable_satellite_cmd = InstallerCommand(
    installer_args=[
        'enable-foreman-plugin-puppet',
        'enable-foreman-cli-puppet',
        'enable-puppet',
    ],
    installer_opts={
        'foreman-proxy-puppet': 'true',
        'puppet-server': 'true',
        'puppet-server-foreman-ssl-ca': '/etc/pki/katello/puppet/puppet_client_ca.crt',
        'puppet-server-foreman-ssl-cert': '/etc/pki/katello/puppet/puppet_client.crt',
        'puppet-server-foreman-ssl-key': '/etc/pki/katello/puppet/puppet_client.key',
    },
)

enable_capsule_cmd = InstallerCommand(
    installer_args=[
        'enable-puppet',
    ],
    installer_opts={
        'foreman-proxy-puppet': 'true',
        'puppet-server': 'true',
        'puppet-server-foreman-ssl-ca': '/etc/pki/katello/puppet/puppet_client_ca.crt',
        'puppet-server-foreman-ssl-cert': '/etc/pki/katello/puppet/puppet_client.crt',
        'puppet-server-foreman-ssl-key': '/etc/pki/katello/puppet/puppet_client.key',
    },
)


@pytest.fixture(scope='module')
def module_puppet_enabled_sat(module_destructive_sat):
    """Satellite with enabled puppet plugin"""
    module_destructive_sat.register_to_dogfood()
    result = module_destructive_sat.execute(enable_satellite_cmd.get_command(), timeout=900000)
    assert result.status == 0
    module_destructive_sat.execute('hammer -r')  # workaround for BZ#2039696
    yield module_destructive_sat


@pytest.fixture(scope='module')
def module_puppet_org(module_puppet_enabled_sat):
    yield module_puppet_enabled_sat.api.Organization().create()


@pytest.fixture(scope='module')
def module_puppet_loc(module_puppet_enabled_sat):
    yield module_puppet_enabled_sat.api.Location().create()


@pytest.fixture(scope='session')
def default_puppet_environment(module_puppet_org, module_puppet_enabled_sat):
    environments = module_puppet_enabled_sat.api.Environment().search(
        query=dict(search=f'organization_id={module_puppet_org.id}')
    )
    if environments:
        return environments[0].read()


@pytest.fixture(scope='module')
def module_puppet_environment(module_puppet_org, module_puppet_loc, module_puppet_enabled_sat):
    environment = module_puppet_enabled_sat.api.Environment(
        organization=[module_puppet_org], location=[module_puppet_loc]
    ).create()
    return module_puppet_enabled_sat.api.Environment(id=environment.id).read()


@pytest.mark.skipif((not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url')
@pytest.fixture(scope='module')
def module_import_puppet_module(module_puppet_enabled_sat):
    """Returns custom puppet environment name that contains imported puppet module
    and puppet class name."""
    puppet_class = 'generic_1'
    return {
        'puppet_class': puppet_class,
        'env': module_puppet_enabled_sat.create_custom_environment(repo=puppet_class),
    }


@pytest.fixture(scope='module')
def module_env_search(
    module_puppet_org, module_puppet_loc, module_import_puppet_module, module_puppet_enabled_sat
):
    """Search for puppet environment created from module_import_puppet_module fixture.

    Returns the puppet environment with updated organization and location.
    """
    env = (
        module_puppet_enabled_sat.api.Environment()
        .search(query={'search': f'name={module_import_puppet_module["env"]}'})[0]
        .read()
    )
    env.location = [module_puppet_loc]
    env.organization = [module_puppet_org]
    env.update(['location', 'organization'])
    return env


@pytest.fixture(scope='module')
def module_puppet_classes(
    module_env_search, module_import_puppet_module, module_puppet_enabled_sat
):
    """Returns puppet class based on following criteria:
    Puppet environment from module_env_search and puppet class name.
    """
    return module_puppet_enabled_sat.api.PuppetClass().search(
        query={
            'search': f'name ~ {module_import_puppet_module["puppet_class"]} '
            f'and environment = {module_env_search.name}'
        }
    )
