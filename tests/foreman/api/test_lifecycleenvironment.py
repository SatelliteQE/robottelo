"""Unit tests for the ``environments`` paths.

Documentation for these paths is available here:
http://www.katello.org/docs/api/apidoc/lifecycle_environments.html


:Requirement: Lifecycleenvironment

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: LifecycleEnvironments

:Assignee: ltran

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.constants import ENVIRONMENT
from robottelo.utils.datafactory import invalid_names_list
from robottelo.utils.datafactory import parametrized
from robottelo.utils.datafactory import valid_data_list


@pytest.fixture(scope='module')
def module_lce(module_org):
    return entities.LifecycleEnvironment(
        organization=module_org, description=gen_string('alpha')
    ).create()


@pytest.fixture
def lce(module_org):
    return entities.LifecycleEnvironment(organization=module_org).create()


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_name(name):
    """Create lifecycle environment with valid name only

    :id: ec1d985a-6a39-4de6-b635-c803ecedd832

    :expectedresults: Lifecycle environment is created and has proper name

    :CaseImportance: Critical

    :parametrized: yes
    """
    assert entities.LifecycleEnvironment(name=name).create().name == name


@pytest.mark.parametrize('desc', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_description(desc):
    """Create lifecycle environment with valid description

    :id: 0bc05510-afc7-4087-ab75-1065ab5ba1d3

    :expectedresults: Lifecycle environment is created and has proper
        description

    :CaseImportance: Critical

    :parametrized: yes
    """
    assert entities.LifecycleEnvironment(description=desc).create().description == desc


@pytest.mark.tier1
def test_positive_create_prior(module_org):
    """Create a lifecycle environment with valid name with Library as
    prior

    :id: 66d34781-8210-4282-8b5e-4be811d5c756

    :expectedresults: Lifecycle environment is created with Library as
        prior

    :CaseImportance: Critical
    """
    lc_env = entities.LifecycleEnvironment(organization=module_org).create()
    assert lc_env.prior.read().name == ENVIRONMENT


@pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
@pytest.mark.tier3
def test_negative_create_with_invalid_name(name):
    """Create lifecycle environment providing an invalid name

    :id: 7e8ea2e6-5927-4e86-8ea8-04c3feb524a6

    :expectedresults: Lifecycle environment is not created

    :CaseImportance: Low

    :parametrized: yes
    """
    with pytest.raises(HTTPError):
        entities.LifecycleEnvironment(name=name).create()


@pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_update_name(module_lce, new_name):
    """Create lifecycle environment providing the initial name, then
    update its name to another valid name.

    :id: b6715e02-f15e-4ab8-8b13-18a3619fee9e

    :expectedresults: Lifecycle environment is created and updated properly

    :parametrized: yes
    """
    module_lce.name = new_name
    module_lce.update(['name'])
    updated = entities.LifecycleEnvironment(id=module_lce.id).read()
    assert new_name == updated.name


@pytest.mark.parametrize('new_desc', **parametrized(valid_data_list()))
@pytest.mark.tier2
def test_positive_update_description(module_lce, new_desc):
    """Create lifecycle environment providing the initial
    description, then update its description to another one.

    :id: e946b1fc-f79f-4e57-9d4a-3181a276222b

    :expectedresults: Lifecycle environment is created and updated properly

    :CaseLevel: Integration

    :CaseImportance: Low

    :parametrized: yes
    """
    module_lce.description = new_desc
    module_lce.update(['description'])
    updated = entities.LifecycleEnvironment(id=module_lce.id).read()
    assert new_desc == updated.description


@pytest.mark.parametrize('new_name', **parametrized(invalid_names_list()))
@pytest.mark.tier1
def test_negative_update_name(module_lce, new_name):
    """Update lifecycle environment providing an invalid name

    :id: 55723382-9d98-43c8-85fb-df4702ca7478

    :expectedresults: Lifecycle environment is not updated and
        corresponding error is raised

    :CaseImportance: Low

    :parametrized: yes
    """
    with pytest.raises(HTTPError):
        module_lce.name = new_name
        module_lce.update(['name'])
    lce = module_lce.read()
    assert lce.name != new_name


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete(lce, name):
    """Create lifecycle environment and then delete it.

    :id: cd5a97ca-c1e8-41c7-8d6b-f908916b24e1

    :expectedresults: Lifecycle environment is deleted successfully

    :CaseImportance: Critical

    :parametrized: yes
    """
    lce.delete()
    with pytest.raises(HTTPError):
        entities.LifecycleEnvironment(id=lce.id).read()


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier2
def test_positive_search_in_org(name):
    """Search for a lifecycle environment and specify an org ID.

    :id: 110e4777-c374-4365-b676-b1db4552fe51

    :Steps:

        1. Create an organization.
        2. Create a lifecycle environment belonging to the organization.
        3. Search for lifecycle environments in the organization.

    :expectedresults: Only "Library" and the lifecycle environment just
        created are in the search results.

    :CaseLevel: Integration

    :parametrized: yes
    """
    new_org = entities.Organization().create()
    lc_env = entities.LifecycleEnvironment(organization=new_org).create()
    lc_envs = lc_env.search({'organization'})
    assert len(lc_envs) == 2
    assert {lc_env_.name for lc_env_ in lc_envs}, {'Library', lc_env.name}


@pytest.mark.tier2
@pytest.mark.stubbed('Implement once BZ1348727 is fixed')
def test_positive_create_environment_after_host_register():
    """Verify that no error is thrown when creating an environment after
    registering a host to Library.

    :id: ceedf88d-1ad1-47ff-aab1-04587a8121ee

    :BZ: 1348727

    :Setup:
        1. Create an organization.
        2. Create a new content host.
        3. Register the content host to the Library environment.

    :Steps: Create a new environment.

    :expectedresults: The environment is created without any errors.

    :CaseLevel: Integration

    :CaseAutomation: NotAutomated
    """
