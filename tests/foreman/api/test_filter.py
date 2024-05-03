"""Unit tests for the ``filters`` paths.

An API reference is available here:
http://theforeman.org/api/apidoc/v2/filters.html


:Requirement: Filter

:CaseAutomation: Automated

:CaseComponent: UsersRoles

:Team: Endeavour

:CaseImportance: High

"""

import pytest
from requests.exceptions import HTTPError


@pytest.fixture(scope='module')
def module_perms(module_target_sat):
    """Search for provisioning template permissions. Set ``cls.ct_perms``."""
    return module_target_sat.api.Permission().search(
        query={'search': 'resource_type="ProvisioningTemplate"'}
    )


@pytest.mark.tier1
def test_positive_create_with_permission(module_perms, module_target_sat):
    """Create a filter and assign it some permissions.

    :id: b8631d0a-a71a-41aa-9f9a-d12d62adc496

    :expectedresults: The created filter has the assigned permissions.

    :CaseImportance: Critical
    """
    # Create a filter and assign all ProvisioningTemplate permissions to it
    filter_ = module_target_sat.api.Filter(permission=module_perms).create()
    filter_perms = [perm.id for perm in filter_.permission]
    perms = [perm.id for perm in module_perms]
    assert filter_perms == perms


@pytest.mark.tier1
def test_positive_delete(module_perms, module_target_sat):
    """Create a filter and delete it afterwards.

    :id: f0c56fd8-c91d-48c3-ad21-f538313b17eb

    :expectedresults: The deleted filter cannot be fetched.

    :CaseImportance: Critical
    """
    filter_ = module_target_sat.api.Filter(permission=module_perms).create()
    filter_.delete()
    with pytest.raises(HTTPError):
        filter_.read()


@pytest.mark.tier1
def test_positive_delete_role(module_perms, module_target_sat):
    """Create a filter and delete the role it points at.

    :id: b129642d-926d-486a-84d9-5952b44ac446

    :expectedresults: The filter cannot be fetched.

    :CaseImportance: Critical
    """
    role = module_target_sat.api.Role().create()
    filter_ = module_target_sat.api.Filter(permission=module_perms, role=role).create()

    # A filter depends on a role. Deleting a role implicitly deletes the
    # filter pointing at it.
    role.delete()
    with pytest.raises(HTTPError):
        role.read()
    with pytest.raises(HTTPError):
        filter_.read()
