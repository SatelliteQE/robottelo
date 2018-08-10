# -*- encoding: utf-8 -*-
# pylint: disable=no-self-use
"""Test class for Realm CLI

:Requirement: Realm

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: CLI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import random

from fauxfactory import gen_string
from robottelo.cleanup import capsule_cleanup, realm_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    make_proxy,
    make_realm,
    CLIFactoryError,
)
from robottelo.cli.realm import Realm
from robottelo.decorators import tier1, run_in_one_thread, upgrade
from robottelo.test import CLITestCase


@run_in_one_thread
class RealmTestCase(CLITestCase):
    """Tests for Realms via Hammer CLI, must be run on QE RHEL7 Sat6.3 host"""

    def _make_proxy(self, options=None):
        """Create a Proxy and register the cleanup function"""
        proxy = make_proxy(options=options)
        # Add capsule to cleanup list
        self.addCleanup(capsule_cleanup, proxy['id'])
        return proxy

    def setUp(self):
        self.realm = None
        self.realm_name = gen_string('alpha', random.randint(1, 30))

    def tearDown(self):
        """Delete realm from proxy after test completes"""
        if self.realm:
            self.addCleanup(realm_cleanup, self.realm['id'])

    @tier1
    @upgrade
    def test_positive_delete_by_name(self):
        """Realm deletion by realm name

        :id: ef3967e6-d53d-4dec-b74f-c20448d5fc6d

        :expectedresults: Realm is deleted
        """
        proxy = self._make_proxy()
        realm = make_realm({
            'realm-proxy-id': proxy['id'],
            'realm-type': 'Active Directory'
        })
        Realm.delete({'name': realm['name']})
        with self.assertRaises(CLIReturnCodeError):
            Realm.info({'id': realm['id']})

    @tier1
    def test_positive_delete_by_id(self):
        """Realm deletion by realm id

        :id: 7c1aca0e-9724-40de-b38f-9189bdae0514

        :expectedresults: Realm is deleted
        """
        proxy = self._make_proxy()
        realm = make_realm({
            'realm-proxy-id': proxy['id'],
            'realm-type': 'Active Directory'
        })
        Realm.delete({'id': realm['id']})
        with self.assertRaises(CLIReturnCodeError):
            Realm.info({'id': realm['id']})

    @tier1
    def test_positive_realm_info_name(self):
        """Test realm info functionality

        :id: 2e3e92df-61f3-4c6b-98b9-dc9c2f8d140c

        :expectedresults: Realm info information from name is correct
        """
        proxy = self._make_proxy()
        self.realm = make_realm({
            'name': self.realm_name,
            'realm-proxy-id': proxy['id'],
            'realm-type': 'Red Hat Identity Management',
            'locations': proxy['locations']
        })
        info = Realm.info({'name': self.realm['name']})
        for key in info.keys():
            self.assertEquals(info[key], self.realm[key])

    @tier1
    def test_positive_realm_info_id(self):
        """Test realm info functionality

        :id: 1ae7b3af-221e-4480-9e93-d05d573456b4

        :expectedresults: Realm info information from ID is correct
        """
        proxy = self._make_proxy()
        self.realm = make_realm({
            'name': self.realm_name,
            'realm-proxy-id': proxy['id'],
            'realm-type': 'Red Hat Identity Management',
            'locations': proxy['locations']
        })
        info = Realm.info({'id': self.realm['id']})
        for key in info.keys():
            self.assertEquals(info[key], self.realm[key])
        self.assertEquals(info, Realm.info({'id': self.realm['id']}))

    @tier1
    def test_positive_realm_update_name(self):
        """Test updating realm name

        :id: c09e6599-c77a-4290-ac93-311d06e3d860

        :expectedresults: Realm name updated
        """
        realm_name = gen_string('alphanumeric')
        new_realm_name = self.realm_name
        proxy = self._make_proxy()
        self.realm = make_realm({
            'name': realm_name,
            'realm-proxy-id': proxy['id'],
            'realm-type': 'Red Hat Identity Management',
            'locations': proxy['locations']
        })
        self.assertEquals(self.realm['name'], realm_name)
        up = Realm.update({'id': self.realm['id'], 'new-name': new_realm_name})
        self.assertEquals(
            up[0]['message'],
            'Realm [{0}] updated.'.format(new_realm_name)
        )
        info = Realm.info({'id': self.realm['id']})
        self.assertEquals(info['name'], new_realm_name)

    @tier1
    def test_negative_realm_update_invalid_type(self):
        """Test updating realm with an invalid type

        :id: 3097f8e5-9152-4d8d-9991-969bdfc9c4d4

        :expectedresults: Realm is not updated
        """
        realm_type = 'Red Hat Identity Management'
        new_realm_type = gen_string('alpha')
        proxy = self._make_proxy()
        self.realm = make_realm({
            'name': self.realm_name,
            'realm-proxy-id': proxy['id'],
            'realm-type': realm_type,
            'locations': proxy['locations']
        })
        with self.assertRaises(CLIReturnCodeError):
            Realm.update({
                'id': self.realm['id'],
                'realm-type': new_realm_type
            })

    @tier1
    def test_negative_create_name_only(self):
        """Create a realm with just a name parameter

        :id: 5606279f-0707-4d36-a307-b204ebb981ad

        :expectedresults: Realm creation fails, requires proxy_id and type
        """
        with self.assertRaises(CLIFactoryError):
            make_realm({'name': self.realm_name})

    @tier1
    def test_negative_create_invalid_id(self):
        """Create a realm with an invalid proxy id

        :id: 916bd1fb-4649-469c-b511-b0b07301a990

        :expectedresults: Realm creation fails, proxy_id must be numeric
        """
        with self.assertRaises(CLIFactoryError):
            make_realm({
                'name': self.realm_name,
                'realm-proxy-id': gen_string('alphanumeric'),
                'realm-type': 'Red Hat Identity Management'
            })

    @tier1
    def test_negative_create_invalid_realm_type(self):
        """Create a realm with an invalid type

        :id: 423a0969-9311-48d2-9220-040a42159a89

        :expectedresults: Realm creation fails, type must be in list
            e.g. Red Hat Identity Management or Active Directory
        """
        with self.assertRaises(CLIFactoryError):
            make_realm({
                'name': self.realm_name,
                'realm-proxy-id': '1',
                'realm-type': gen_string('alpha')
            })

    @tier1
    def test_negative_create_invalid_location(self):
        """Create a realm with an invalid location

        :id: 95335c3a-413f-4156-b727-91b525738171

        :expectedresults: Realm creation fails, location not found
        """
        with self.assertRaises(CLIFactoryError):
            make_realm({
                'name': self.realm_name,
                'realm-proxy-id': '1',
                'locations': 'Raleigh, NC',
                'realm-type': 'Red Hat Identity Management'
            })

    @tier1
    def test_negative_create_invalid_organization(self):
        """Create a realm with an invalid organization

        :id: c0ffbc6d-a2da-484b-9627-5454687a3abb

        :expectedresults: Realm creation fails, organization not found
        """
        with self.assertRaises(CLIFactoryError):
            make_realm({
                'name': self.realm_name,
                'realm-proxy-id': '1',
                'organizations': gen_string('alphanumeric', 20),
                'realm-type': 'Red Hat Identity Management'
            })

    @tier1
    def test_negative_delete_nonexistent_realm_name(self):
        """Delete a realm with a name that does not exist

        :id: 616db509-9643-4817-ba6b-f05cdb1cecb0

        :expectedresults: Realm not found
        """
        with self.assertRaises(CLIReturnCodeError):
            Realm.delete({'name': self.realm_name})

    @tier1
    def test_negative_delete_nonexistent_realm_id(self):
        """Delete a realm with an id that does not exist

        :id: 70bb9d4e-7e71-479a-8c82-e6fcff88ea14

        :expectedresults: Realm not found
        """
        with self.assertRaises(CLIReturnCodeError):
            Realm.delete({'id': 0})

    @tier1
    def test_negative_info_nonexistent_realm_name(self):
        """Get info for a realm with a name that does not exist

        :id: 24e4fbfa-7141-4f90-8c5d-eb88b162bd64

        :expectedresults: Realm not found
        """
        with self.assertRaises(CLIReturnCodeError):
            Realm.info({'name': self.realm_name})

    @tier1
    def test_negative_info_nonexistent_realm_id(self):
        """Get info for a realm with an id that does not exists

        :id: db8382eb-6d0b-4d6a-a9bf-38a462389f7b

        :expectedresults: Realm not found
        """
        with self.assertRaises(CLIReturnCodeError):
            Realm.info({'id': 0})
