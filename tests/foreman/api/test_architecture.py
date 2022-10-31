"""Unit tests for the ``architectures`` paths.

:Requirement: Architecture

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Hosts

:Assignee: pdragun

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from fauxfactory import gen_choice
from nailgun import entities
from requests.exceptions import HTTPError

from robottelo.utils.datafactory import invalid_names_list
from robottelo.utils.datafactory import parametrized
from robottelo.utils.datafactory import valid_data_list


@pytest.mark.tier1
def test_positive_CRUD(default_os):
    """Create a new Architecture with several attributes, update the name
    and delete the Architecture itself.

    :id: 80bca2c0-a6a1-4676-a036-bd918812d600

    :expectedresults: Architecture should be created, modified and deleted successfully
        with given attributes.

    :CaseImportance: Critical
    """

    # Create
    name = gen_choice(list(valid_data_list().values()))
    arch = entities.Architecture(name=name, operatingsystem=[default_os]).create()
    assert {default_os.id} == {os.id for os in arch.operatingsystem}
    assert name == arch.name

    # Update
    name = gen_choice(list(valid_data_list().values()))
    arch = entities.Architecture(id=arch.id, name=name).update(['name'])
    assert name == arch.name

    # Delete
    arch.delete()
    with pytest.raises(HTTPError):
        arch.read()


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
def test_negative_create_with_invalid_name(name):
    """Create architecture providing an invalid initial name.

    :id: 0fa6377d-063a-4e24-b606-b342e0d9108b

    :parametrized: yes

    :expectedresults: Architecture is not created

    :CaseImportance: Medium

    :BZ: 1401519
    """
    with pytest.raises(HTTPError):
        entities.Architecture(name=name).create()


@pytest.mark.tier1
@pytest.mark.parametrize('name', **parametrized(invalid_names_list()))
def test_negative_update_with_invalid_name(name, module_architecture):
    """Update architecture's name to an invalid name.

    :id: cb27b69b-14e0-42d0-9e44-e09d68324803

    :parametrized: yes

    :expectedresults: Architecture's name is not updated.

    :CaseImportance: Medium
    """
    with pytest.raises(HTTPError):
        entities.Architecture(id=module_architecture.id, name=name).update(['name'])
    arch = entities.Architecture(id=module_architecture.id).read()
    assert arch.name != name
