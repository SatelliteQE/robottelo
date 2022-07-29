"""Test class for Realm CLI

:Requirement: Realm

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Realm

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

import pytest
from fauxfactory import gen_string

from robottelo.cli.base import CLIReturnCodeError


pytestmark = [pytest.mark.run_in_one_thread, pytest.mark.destructive]


def test_positive_delete_by_name(
    module_subscribe_satellite,
    module_enroll_idm_and_configure_external_auth,
    configure_realm,
    module_fake_proxy,
    module_target_sat,
):
    """Realm deletion by realm name

    :id: ef3967e6-d53d-4dec-b74f-c20448d5fc6d

    :expectedresults: Realm is deleted
    """
    realm = module_target_sat.cli_factory.make_realm(
        {'realm-proxy-id': module_fake_proxy.id, 'realm-type': 'Active Directory'}
    )
    module_target_sat.cli.Realm.delete({'name': realm['name']})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Realm.info({'id': realm['id']})


def test_positive_delete_by_id(
    module_subscribe_satellite,
    module_enroll_idm_and_configure_external_auth,
    configure_realm,
    module_fake_proxy,
    module_target_sat,
):
    """Realm deletion by realm ID

    :id: 7c1aca0e-9724-40de-b38f-9189bdae0514

    :expectedresults: Realm is deleted
    """
    realm = module_target_sat.cli_factory.make_realm(
        {'realm-proxy-id': module_fake_proxy.id, 'realm-type': 'Active Directory'}
    )
    module_target_sat.cli.Realm.delete({'id': realm['id']})
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Realm.info({'id': realm['id']})


def test_positive_realm_info_name(
    module_subscribe_satellite,
    module_enroll_idm_and_configure_external_auth,
    configure_realm,
    module_fake_proxy,
    request,
    module_target_sat,
):
    """Test realm info functionality

    :id: 2e3e92df-61f3-4c6b-98b9-dc9c2f8d140c

    :expectedresults: Realm information obtained by name is correct
    """
    realm = module_target_sat.cli_factory.make_realm(
        {
            'name': gen_string('alpha', random.randint(1, 30)),
            'realm-proxy-id': module_fake_proxy.id,
            'realm-type': 'Red Hat Identity Management',
            'locations': [loc.read().name for loc in module_fake_proxy.location],
        }
    )
    request.addfinalizer(lambda: module_target_sat.cli.Realm(realm['id']).delete())
    info = module_target_sat.cli.Realm.info({'name': realm['name']})
    for key in info.keys():
        assert info[key] == realm[key]


def test_positive_realm_info_id(
    module_subscribe_satellite,
    module_enroll_idm_and_configure_external_auth,
    configure_realm,
    module_fake_proxy,
    request,
    module_target_sat,
):
    """Test realm info functionality

    :id: 1ae7b3af-221e-4480-9e93-d05d573456b4

    :expectedresults: Realm information obtained by ID is correct
    """
    realm = module_target_sat.cli_factory.make_realm(
        {
            'name': gen_string('alpha', random.randint(1, 30)),
            'realm-proxy-id': module_fake_proxy.id,
            'realm-type': 'Red Hat Identity Management',
            'locations': [loc.read().name for loc in module_fake_proxy.location],
        }
    )
    request.addfinalizer(lambda: module_target_sat.cli.Realm(realm['id']).delete())
    info = module_target_sat.cli.Realm.info({'id': realm['id']})
    for key in info.keys():
        assert info[key] == realm[key]
    assert info == module_target_sat.cli.Realm.info({'id': realm['id']})


def test_positive_realm_update_name(
    module_subscribe_satellite,
    module_enroll_idm_and_configure_external_auth,
    configure_realm,
    module_fake_proxy,
    request,
    module_target_sat,
):
    """Test updating realm name

    :id: c09e6599-c77a-4290-ac93-311d06e3d860

    :expectedresults: Realm name can be updated
    """
    realm_name = gen_string('alpha', random.randint(1, 30))
    new_realm_name = gen_string('alpha', random.randint(1, 30))
    realm = module_target_sat.cli_factory.make_realm(
        {
            'name': realm_name,
            'realm-proxy-id': module_fake_proxy.id,
            'realm-type': 'Red Hat Identity Management',
            'locations': [loc.read().name for loc in module_fake_proxy.location],
        }
    )
    request.addfinalizer(lambda: module_target_sat.cli.Realm(realm['id']).delete())
    assert realm['name'] == realm_name
    up = module_target_sat.cli.Realm.update({'id': realm['id'], 'new-name': new_realm_name})
    assert up[0]['message'] == f'Realm [{new_realm_name}] updated.'
    info = module_target_sat.cli.Realm.info({'id': realm['id']})
    assert info['name'] == new_realm_name


def test_negative_realm_update_invalid_type(
    module_subscribe_satellite,
    module_enroll_idm_and_configure_external_auth,
    configure_realm,
    module_fake_proxy,
    request,
    module_target_sat,
):
    """Test updating realm with an invalid type

    :id: 3097f8e5-9152-4d8d-9991-969bdfc9c4d4

    :expectedresults: Realm is not updated
    """
    realm_type = 'Red Hat Identity Management'
    new_realm_type = gen_string('alpha')
    realm = module_target_sat.cli_factory.make_realm(
        {
            'name': gen_string('alpha', random.randint(1, 30)),
            'realm-proxy-id': module_fake_proxy.id,
            'realm-type': realm_type,
            'locations': [loc.read().name for loc in module_fake_proxy.location],
        }
    )
    request.addfinalizer(lambda: module_target_sat.cli.Realm(realm['id']).delete())
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Realm.update({'id': realm['id'], 'realm-type': new_realm_type})
