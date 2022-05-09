# Puppet Environment fixtures
import pytest
from nailgun import entities

from robottelo.config import settings


@pytest.fixture(scope='session')
def default_puppet_environment(module_org):
    environments = entities.Environment().search(
        query=dict(search=f'organization_id={module_org.id}')
    )
    if environments:
        return environments[0].read()


@pytest.fixture(scope='module')
def module_puppet_environment(module_org, module_location):
    environment = entities.Environment(
        organization=[module_org], location=[module_location]
    ).create()
    return entities.Environment(id=environment.id).read()


@pytest.mark.skipif((not settings.robottelo.repos_hosting_url), reason='Missing repos_hosting_url')
@pytest.fixture(scope='module')
def module_import_puppet_module(module_target_sat):
    """Returns custom puppet environment name that contains imported puppet module
    and puppet class name."""
    puppet_class = 'generic_1'
    return {
        'puppet_class': puppet_class,
        'env': module_target_sat.create_custom_environment(repo=puppet_class),
    }


@pytest.fixture(scope='module')
def module_env_search(module_org, module_location, module_import_puppet_module):
    """Search for puppet environment created from module_import_puppet_module fixture.

    Returns the puppet environment with updated organization and location.
    """
    env = (
        entities.Environment()
        .search(query={'search': f'name={module_import_puppet_module["env"]}'})[0]
        .read()
    )
    env.location = [module_location]
    env.organization = [module_org]
    env.update(['location', 'organization'])
    return env


@pytest.fixture(scope='module')
def module_puppet_classes(module_env_search, module_import_puppet_module):
    """Returns puppet class based on following criteria:
    Puppet environment from module_env_search and puppet class name.
    """
    return entities.PuppetClass().search(
        query={
            'search': f'name ~ {module_import_puppet_module["puppet_class"]} '
            f'and environment = {module_env_search.name}'
        }
    )
