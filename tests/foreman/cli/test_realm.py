"""Test class for Realm CLI

:Requirement: Realm

:CaseAutomation: Automated

:CaseComponent: Authentication

:Team: Endeavour

:CaseImportance: High

"""

import random

from fauxfactory import gen_string
import pytest

from robottelo.exceptions import CLIFactoryError, CLIReturnCodeError


def test_negative_create_name_only(module_target_sat):
    """Create a realm with just a name parameter

    :id: 5606279f-0707-4d36-a307-b204ebb981ad

    :expectedresults: Realm creation fails, requires proxy_id and type
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.realm({'name': gen_string('alpha', random.randint(1, 30))})


def test_negative_create_invalid_proxy_id(module_target_sat):
    """Create a realm with an invalid proxy ID

    :id: 916bd1fb-4649-469c-b511-b0b07301a990

    :expectedresults: Realm creation fails, proxy_id must be numeric
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.realm(
            {
                'name': gen_string('alpha', random.randint(1, 30)),
                'realm-proxy-id': gen_string('alphanumeric'),
                'realm-type': 'Red Hat Identity Management',
            }
        )


def test_negative_create_invalid_realm_type(module_target_sat):
    """Create a realm with an invalid type

    :id: 423a0969-9311-48d2-9220-040a42159a89

    :expectedresults: Realm creation fails, type must be in list
        e.g. Red Hat Identity Management or Active Directory
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.realm(
            {
                'name': gen_string('alpha', random.randint(1, 30)),
                'realm-proxy-id': '1',
                'realm-type': gen_string('alpha'),
            }
        )


def test_negative_create_invalid_location(module_target_sat):
    """Create a realm with an invalid location

    :id: 95335c3a-413f-4156-b727-91b525738171

    :expectedresults: Realm creation fails, location not found
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.realm(
            {
                'name': gen_string('alpha', random.randint(1, 30)),
                'realm-proxy-id': '1',
                'locations': 'Raleigh, NC',
                'realm-type': 'Red Hat Identity Management',
            }
        )


def test_negative_create_invalid_organization(module_target_sat):
    """Create a realm with an invalid organization

    :id: c0ffbc6d-a2da-484b-9627-5454687a3abb

    :expectedresults: Realm creation fails, organization not found
    """
    with pytest.raises(CLIFactoryError):
        module_target_sat.cli_factory.realm(
            {
                'name': gen_string('alpha', random.randint(1, 30)),
                'realm-proxy-id': '1',
                'organizations': gen_string('alphanumeric', 20),
                'realm-type': 'Red Hat Identity Management',
            }
        )


def test_negative_delete_nonexistent_realm_name(module_target_sat):
    """Delete a realm with a name that does not exist

    :id: 616db509-9643-4817-ba6b-f05cdb1cecb0

    :expectedresults: Realm not found
    """
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Realm.delete({'name': gen_string('alpha', random.randint(1, 30))})


def test_negative_delete_nonexistent_realm_id(module_target_sat):
    """Delete a realm with an ID that does not exist

    :id: 70bb9d4e-7e71-479a-8c82-e6fcff88ea14

    :expectedresults: Realm not found
    """
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Realm.delete({'id': 0})


def test_negative_info_nonexistent_realm_name(module_target_sat):
    """Get info for a realm with a name that does not exist

    :id: 24e4fbfa-7141-4f90-8c5d-eb88b162bd64

    :expectedresults: Realm not found
    """
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Realm.info({'name': gen_string('alpha', random.randint(1, 30))})


def test_negative_info_nonexistent_realm_id(module_target_sat):
    """Get info for a realm with an ID that does not exist

    :id: db8382eb-6d0b-4d6a-a9bf-38a462389f7b

    :expectedresults: Realm not found
    """
    with pytest.raises(CLIReturnCodeError):
        module_target_sat.cli.Realm.info({'id': 0})
