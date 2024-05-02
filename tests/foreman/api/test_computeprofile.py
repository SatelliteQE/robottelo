"""Unit tests for the Compute Profile feature.

:Requirement: Computeprofile

:CaseAutomation: Automated

:CaseComponent: ComputeResources

:Team: Rocket

:CaseImportance: High

"""

import pytest
from requests.exceptions import HTTPError

from robottelo.utils.datafactory import (
    invalid_values_list,
    parametrized,
    valid_data_list,
)


@pytest.mark.parametrize('name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_create_with_name(name, target_sat):
    """Create new Compute Profile using different names

    :id: 97d04911-9368-4674-92c7-1e3ff114bc18

    :expectedresults: Compute Profile is created

    :CaseImportance: Critical

    :parametrized: yes
    """
    profile = target_sat.api.ComputeProfile(name=name).create()
    assert name == profile.name


@pytest.mark.parametrize('name', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_create(name, target_sat):
    """Attempt to create Compute Profile using invalid names only

    :id: 2d34a1fd-70a5-4e59-b2e2-86fbfe8e31ab

    :expectedresults: Compute Profile is not created

    :CaseImportance: Critical

    :parametrized: yes
    """
    with pytest.raises(HTTPError):
        target_sat.api.ComputeProfile(name=name).create()


@pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_update_name(new_name, target_sat):
    """Update selected Compute Profile entity using proper names

    :id: c79193d7-2e0f-4ed9-b947-05feeddabfda

    :expectedresults: Compute Profile is updated.

    :CaseImportance: Critical

    :parametrized: yes
    """
    profile = target_sat.api.ComputeProfile().create()
    target_sat.api.ComputeProfile(id=profile.id, name=new_name).update(['name'])
    updated_profile = target_sat.api.ComputeProfile(id=profile.id).read()
    assert new_name == updated_profile.name


@pytest.mark.parametrize('new_name', **parametrized(invalid_values_list()))
@pytest.mark.tier1
def test_negative_update_name(new_name, target_sat):
    """Attempt to update Compute Profile entity using invalid names only

    :id: 042b40d5-a78b-4e65-b5cb-5b270b800b37

    :expectedresults: Compute Profile is not updated.

    :CaseImportance: Critical

    :parametrized: yes
    """
    profile = target_sat.api.ComputeProfile().create()
    with pytest.raises(HTTPError):
        target_sat.api.ComputeProfile(id=profile.id, name=new_name).update(['name'])
    updated_profile = target_sat.api.ComputeProfile(id=profile.id).read()
    assert new_name != updated_profile.name


@pytest.mark.parametrize('new_name', **parametrized(valid_data_list()))
@pytest.mark.tier1
def test_positive_delete(new_name, target_sat):
    """Delete Compute Profile entity

    :id: 0a620e23-7ba6-4178-af7a-fd1e332f478f

    :expectedresults: Compute Profile is deleted successfully.

    :CaseImportance: Critical

    :parametrized: yes
    """
    profile = target_sat.api.ComputeProfile(name=new_name).create()
    profile.delete()
    with pytest.raises(HTTPError):
        target_sat.api.ComputeProfile(id=profile.id).read()
