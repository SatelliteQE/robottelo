# Lifecycle Environment Fixtures
import pytest

from robottelo.constants import ENVIRONMENT


@pytest.fixture(scope='session')
def default_lce(session_target_sat):
    return session_target_sat.api.LifecycleEnvironment().search(
        query={'search': f'name="{ENVIRONMENT}"'}
    )[0]


@pytest.fixture(scope='module')
def module_lce(module_org, module_target_sat):
    return module_target_sat.api.LifecycleEnvironment(organization=module_org).create()


@pytest.fixture(scope='function')
def function_lce(function_org, target_sat):
    return target_sat.api.LifecycleEnvironment(organization=function_org).create()


@pytest.fixture(scope='module')
def module_lce_library(module_org, module_target_sat):
    """Returns the Library lifecycle environment from chosen organization"""
    return (
        module_target_sat.api.LifecycleEnvironment()
        .search(query={'search': f'name={ENVIRONMENT} and organization_id={module_org.id}'})[0]
        .read()
    )


@pytest.fixture(scope='function')
def function_lce_library(function_org, target_sat):
    """Returns the Library lifecycle environment from chosen organization"""
    return (
        target_sat.api.LifecycleEnvironment()
        .search(query={'search': f'name={ENVIRONMENT} and organization_id={function_org.id}'})[0]
        .read()
    )
