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

from robottelo.cleanup import realm_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import CLIFactoryError
from robottelo.cli.factory import make_realm
from robottelo.cli.realm import Realm


pytestmark = [pytest.mark.run_in_one_thread]


@pytest.mark.tier1
def test_positive_delete_by_name(module_fake_proxy):
    """Realm deletion by realm name

    :id: ef3967e6-d53d-4dec-b74f-c20448d5fc6d

    :expectedresults: Realm is deleted
    """
    realm = make_realm({'realm-proxy-id': module_fake_proxy.id, 'realm-type': 'Active Directory'})
    Realm.delete({'name': realm['name']})
    with pytest.raises(CLIReturnCodeError):
        Realm.info({'id': realm['id']})


@pytest.mark.tier1
def test_positive_delete_by_id(module_fake_proxy):
    """Realm deletion by realm ID

    :id: 7c1aca0e-9724-40de-b38f-9189bdae0514

    :expectedresults: Realm is deleted
    """
    realm = make_realm({'realm-proxy-id': module_fake_proxy.id, 'realm-type': 'Active Directory'})
    Realm.delete({'id': realm['id']})
    with pytest.raises(CLIReturnCodeError):
        Realm.info({'id': realm['id']})


@pytest.mark.tier1
def test_positive_realm_info_name(module_fake_proxy, request):
    """Test realm info functionality

    :id: 2e3e92df-61f3-4c6b-98b9-dc9c2f8d140c

    :expectedresults: Realm information obtained by name is correct
    """
    realm = make_realm(
        {
            'name': gen_string('alpha', random.randint(1, 30)),
            'realm-proxy-id': module_fake_proxy.id,
            'realm-type': 'Red Hat Identity Management',
            'locations': [loc.read().name for loc in module_fake_proxy.location],
        }
    )
    request.addfinalizer(lambda: realm_cleanup(realm['id']))
    info = Realm.info({'name': realm['name']})
    for key in info.keys():
        assert info[key] == realm[key]


@pytest.mark.tier1
def test_positive_realm_info_id(module_fake_proxy, request):
    """Test realm info functionality

    :id: 1ae7b3af-221e-4480-9e93-d05d573456b4

    :expectedresults: Realm information obtained by ID is correct
    """
    realm = make_realm(
        {
            'name': gen_string('alpha', random.randint(1, 30)),
            'realm-proxy-id': module_fake_proxy.id,
            'realm-type': 'Red Hat Identity Management',
            'locations': [loc.read().name for loc in module_fake_proxy.location],
        }
    )
    request.addfinalizer(lambda: realm_cleanup(realm['id']))
    info = Realm.info({'id': realm['id']})
    for key in info.keys():
        assert info[key] == realm[key]
    assert info == Realm.info({'id': realm['id']})


@pytest.mark.tier2
def test_positive_realm_update_name(module_fake_proxy, request):
    """Test updating realm name

    :id: c09e6599-c77a-4290-ac93-311d06e3d860

    :expectedresults: Realm name can be updated
    """
    realm_name = gen_string('alpha', random.randint(1, 30))
    new_realm_name = gen_string('alpha', random.randint(1, 30))
    realm = make_realm(
        {
            'name': realm_name,
            'realm-proxy-id': module_fake_proxy.id,
            'realm-type': 'Red Hat Identity Management',
            'locations': [loc.read().name for loc in module_fake_proxy.location],
        }
    )
    request.addfinalizer(lambda: realm_cleanup(realm['id']))
    assert realm['name'] == realm_name
    up = Realm.update({'id': realm['id'], 'new-name': new_realm_name})
    assert up[0]['message'] == f'Realm [{new_realm_name}] updated.'
    info = Realm.info({'id': realm['id']})
    assert info['name'] == new_realm_name


@pytest.mark.tier1
def test_negative_realm_update_invalid_type(module_fake_proxy, request):
    """Test updating realm with an invalid type

    :id: 3097f8e5-9152-4d8d-9991-969bdfc9c4d4

    :expectedresults: Realm is not updated
    """
    realm_type = 'Red Hat Identity Management'
    new_realm_type = gen_string('alpha')
    realm = make_realm(
        {
            'name': gen_string('alpha', random.randint(1, 30)),
            'realm-proxy-id': module_fake_proxy.id,
            'realm-type': realm_type,
            'locations': [loc.read().name for loc in module_fake_proxy.location],
        }
    )
    request.addfinalizer(lambda: realm_cleanup(realm['id']))
    with pytest.raises(CLIReturnCodeError):
        Realm.update({'id': realm['id'], 'realm-type': new_realm_type})


@pytest.mark.tier1
def test_negative_create_name_only():
    """Create a realm with just a name parameter

    :id: 5606279f-0707-4d36-a307-b204ebb981ad

    :expectedresults: Realm creation fails, requires proxy_id and type
    """
    with pytest.raises(CLIFactoryError):
        make_realm({'name': gen_string('alpha', random.randint(1, 30))})


@pytest.mark.tier1
def test_negative_create_invalid_id():
    """Create a realm with an invalid proxy ID

    :id: 916bd1fb-4649-469c-b511-b0b07301a990

    :expectedresults: Realm creation fails, proxy_id must be numeric
    """
    with pytest.raises(CLIFactoryError):
        make_realm(
            {
                'name': gen_string('alpha', random.randint(1, 30)),
                'realm-proxy-id': gen_string('alphanumeric'),
                'realm-type': 'Red Hat Identity Management',
            }
        )


@pytest.mark.tier1
def test_negative_create_invalid_realm_type():
    """Create a realm with an invalid type

    :id: 423a0969-9311-48d2-9220-040a42159a89

    :expectedresults: Realm creation fails, type must be in list
        e.g. Red Hat Identity Management or Active Directory
    """
    with pytest.raises(CLIFactoryError):
        make_realm(
            {
                'name': gen_string('alpha', random.randint(1, 30)),
                'realm-proxy-id': '1',
                'realm-type': gen_string('alpha'),
            }
        )


@pytest.mark.tier1
def test_negative_create_invalid_location():
    """Create a realm with an invalid location

    :id: 95335c3a-413f-4156-b727-91b525738171

    :expectedresults: Realm creation fails, location not found
    """
    with pytest.raises(CLIFactoryError):
        make_realm(
            {
                'name': gen_string('alpha', random.randint(1, 30)),
                'realm-proxy-id': '1',
                'locations': 'Raleigh, NC',
                'realm-type': 'Red Hat Identity Management',
            }
        )


@pytest.mark.tier1
def test_negative_create_invalid_organization():
    """Create a realm with an invalid organization

    :id: c0ffbc6d-a2da-484b-9627-5454687a3abb

    :expectedresults: Realm creation fails, organization not found
    """
    with pytest.raises(CLIFactoryError):
        make_realm(
            {
                'name': gen_string('alpha', random.randint(1, 30)),
                'realm-proxy-id': '1',
                'organizations': gen_string('alphanumeric', 20),
                'realm-type': 'Red Hat Identity Management',
            }
        )


@pytest.mark.tier2
def test_negative_delete_nonexistent_realm_name():
    """Delete a realm with a name that does not exist

    :id: 616db509-9643-4817-ba6b-f05cdb1cecb0

    :expectedresults: Realm not found
    """
    with pytest.raises(CLIReturnCodeError):
        Realm.delete({'name': gen_string('alpha', random.randint(1, 30))})


@pytest.mark.tier2
def test_negative_delete_nonexistent_realm_id():
    """Delete a realm with an ID that does not exist

    :id: 70bb9d4e-7e71-479a-8c82-e6fcff88ea14

    :expectedresults: Realm not found
    """
    with pytest.raises(CLIReturnCodeError):
        Realm.delete({'id': 0})


@pytest.mark.tier2
def test_negative_info_nonexistent_realm_name():
    """Get info for a realm with a name that does not exist

    :id: 24e4fbfa-7141-4f90-8c5d-eb88b162bd64

    :expectedresults: Realm not found
    """
    with pytest.raises(CLIReturnCodeError):
        Realm.info({'name': gen_string('alpha', random.randint(1, 30))})


@pytest.mark.tier2
def test_negative_info_nonexistent_realm_id():
    """Get info for a realm with an ID that does not exist

    :id: db8382eb-6d0b-4d6a-a9bf-38a462389f7b

    :expectedresults: Realm not found
    """
    with pytest.raises(CLIReturnCodeError):
        Realm.info({'id': 0})
