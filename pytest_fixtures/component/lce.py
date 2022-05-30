# Lifecycle Environment Fixtures
import pytest
from nailgun import entities

from robottelo.constants import ENVIRONMENT


@pytest.fixture(scope='session')
def default_lce():
    return entities.LifecycleEnvironment().search(query={'search': f'name="{ENVIRONMENT}"'})[0]


@pytest.fixture(scope='module')
def module_lce(module_org):
    return entities.LifecycleEnvironment(organization=module_org).create()


@pytest.fixture(scope='function')
def function_lce(function_org):
    return entities.LifecycleEnvironment(organization=function_org).create()


@pytest.fixture(scope='module')
def module_lce_library(module_org):
    """Returns the Library lifecycle environment from chosen organization"""
    return (
        entities.LifecycleEnvironment()
        .search(query={'search': f'name={ENVIRONMENT} and organization_id={module_org.id}'})[0]
        .read()
    )


@pytest.fixture(scope='function')
def function_lce_library(function_org):
    """Returns the Library lifecycle environment from chosen organization"""
    return (
        entities.LifecycleEnvironment()
        .search(query={'search': f'name={ENVIRONMENT} and organization_id={function_org.id}'})[0]
        .read()
    )
