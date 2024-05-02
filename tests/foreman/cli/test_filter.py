"""Test for Roles CLI

:Requirement: Filter

:CaseAutomation: Automated

:CaseComponent: UsersRoles

:Team: Endeavour

:CaseImportance: High

"""

import pytest

from robottelo.exceptions import CLIReturnCodeError


@pytest.fixture(scope='module')
def module_perms(module_target_sat):
    """Search for provisioning template permissions. Set ``cls.ct_perms``."""
    return [
        permission['name']
        for permission in module_target_sat.cli.Filter.available_permissions(
            {"search": "resource_type=User"}
        )
    ]


@pytest.fixture
def function_role(target_sat):
    """Create a role that a filter would be assigned"""
    return target_sat.cli_factory.make_role()


@pytest.mark.tier1
def test_positive_create_with_permission(module_perms, function_role, target_sat):
    """Create a filter and assign it some permissions.

    :id: 6da6c5d3-2727-4eb7-aa15-9f7b6f91d3b2

    :expectedresults: The created filter has the assigned permissions.

    :CaseImportance: Critical
    """
    # Assign filter to created role
    filter_ = target_sat.cli_factory.make_filter(
        {'role-id': function_role['id'], 'permissions': module_perms}
    )
    assert set(filter_['permissions'].split(", ")) == set(module_perms)


@pytest.mark.tier1
def test_positive_create_with_org(module_perms, function_role, target_sat):
    """Create a filter and assign it some permissions.

    :id: f6308192-0e1f-427b-a296-b285f6684691

    :expectedresults: The created filter has the assigned permissions.

    :BZ: 1401469

    :CaseImportance: Critical
    """
    org = target_sat.cli_factory.make_org()
    # Assign filter to created role
    filter_ = target_sat.cli_factory.make_filter(
        {
            'role-id': function_role['id'],
            'permissions': module_perms,
            'organization-ids': org['id'],
            'override': 1,
        }
    )
    # we expect here only only one organization, i.e. first element
    assert filter_['organizations'][0] == org['name']


@pytest.mark.tier1
def test_positive_create_with_loc(module_perms, function_role, module_target_sat):
    """Create a filter and assign it some permissions.

    :id: d7d1969a-cb30-4e97-a9a3-3a4aaf608795

    :expectedresults: The created filter has the assigned permissions.

    :BZ: 1401469

    :CaseImportance: Critical
    """
    loc = module_target_sat.cli_factory.make_location()
    # Assign filter to created role
    filter_ = module_target_sat.cli_factory.make_filter(
        {
            'role-id': function_role['id'],
            'permissions': module_perms,
            'location-ids': loc['id'],
            'override': 1,
        }
    )
    # we expect here only only one location, i.e. first element
    assert filter_['locations'][0] == loc['name']


@pytest.mark.tier1
def test_positive_delete(module_perms, function_role, module_target_sat):
    """Create a filter and delete it afterwards.

    :id: 97d1093c-0d49-454b-86f6-f5be87b32775

    :expectedresults: The deleted filter cannot be fetched.

    :CaseImportance: Critical
    """
    filter_ = module_target_sat.cli_factory.make_filter(
        {'role-id': function_role['id'], 'permissions': module_perms}
    )
    module_target_sat.cli.Filter.delete({'id': filter_['id']})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Filter.info({'id': filter_['id']})


@pytest.mark.tier1
@pytest.mark.upgrade
def test_positive_delete_role(module_perms, function_role, target_sat):
    """Create a filter and delete the role it points at.

    :id: e2adb6a4-e408-4912-a32d-2bf2c43187d9

    :expectedresults: The filter cannot be fetched.

    :CaseImportance: Critical
    """
    filter_ = target_sat.cli_factory.make_filter(
        {'role-id': function_role['id'], 'permissions': module_perms}
    )

    # A filter depends on a role. Deleting a role implicitly deletes the
    # filter pointing at it.
    target_sat.cli.Role.delete({'id': function_role['id']})
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Role.info({'id': function_role['id']})
    with pytest.raises(CLIReturnCodeError):
        target_sat.cli.Filter.info({'id': filter_['id']})


@pytest.mark.tier1
def test_positive_update_permissions(module_perms, function_role, target_sat):
    """Create a filter and update its permissions.

    :id: 3d6a52d8-2f8f-4f97-a155-9b52888af16e

    :expectedresults: Permissions updated.

    :CaseImportance: Critical
    """
    filter_ = target_sat.cli_factory.make_filter(
        {'role-id': function_role['id'], 'permissions': module_perms}
    )
    new_perms = [
        permission['name']
        for permission in target_sat.cli.Filter.available_permissions(
            {"search": "resource_type=User"}
        )
    ]
    target_sat.cli.Filter.update({'id': filter_['id'], 'permissions': new_perms})
    filter_ = target_sat.cli.Filter.info({'id': filter_['id']})
    assert set(filter_['permissions'].split(", ")) == set(new_perms)


@pytest.mark.tier1
def test_positive_update_role(module_perms, function_role, target_sat):
    """Create a filter and assign it to another role.

    :id: 2950b3a1-2bce-447f-9df2-869b1d10eaf5

    :expectedresults: Filter is created and assigned to new role.

    :CaseImportance: Critical
    """
    filter_ = target_sat.cli_factory.make_filter(
        {'role-id': function_role['id'], 'permissions': module_perms}
    )
    # Update with another role
    new_role = target_sat.cli_factory.make_role()
    target_sat.cli.Filter.update({'id': filter_['id'], 'role-id': new_role['id']})
    filter_ = target_sat.cli.Filter.info({'id': filter_['id']})
    assert filter_['role'] == new_role['name']


@pytest.mark.tier1
def test_positive_update_org_loc(module_perms, function_role, target_sat):
    """Create a filter and assign it to another organization and location.

    :id: 9bb59109-9701-4ef3-95c6-81f387d372da

    :expectedresults: Filter is created and assigned to new org and loc.

    :BZ: 1401469

    :CaseImportance: Critical
    """
    org = target_sat.cli_factory.make_org()
    loc = target_sat.cli_factory.make_location()
    filter_ = target_sat.cli_factory.make_filter(
        {
            'role-id': function_role['id'],
            'permissions': module_perms,
            'organization-ids': org['id'],
            'location-ids': loc['id'],
            'override': 1,
        }
    )
    # Update org and loc
    new_org = target_sat.cli_factory.make_org()
    new_loc = target_sat.cli_factory.make_location()
    target_sat.cli.Filter.update(
        {
            'id': filter_['id'],
            'permissions': module_perms,
            'organization-ids': new_org['id'],
            'location-ids': new_loc['id'],
            'override': 1,
        }
    )
    filter_ = target_sat.cli.Filter.info({'id': filter_['id']})
    # We expect here only one organization and location
    assert filter_['organizations'][0] == new_org['name']
    assert filter_['locations'][0] == new_loc['name']
