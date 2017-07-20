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
from robottelo.cleanup import capsule_cleanup
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.factory import (
    make_location,
    make_proxy,
    make_realm,
    CLIFactoryError,
)
from robottelo.cli.realm import Realm
from robottelo.decorators import (
    tier1,
)
from robottelo.test import CLITestCase


class RealmTestCase(CLITestCase):
    """Tests for Realms via Hammer CLI, must be run on QE RHEL7 Sat6.3 host"""

    def _make_proxy(self, options=None):
        """Create a Proxy and register the cleanup function"""
        proxy = make_proxy(options=options)
        # Add capsule to cleanup list
        self.addCleanup(capsule_cleanup, proxy['id'])
        return proxy

    @tier1
    def test_positive_create_delete_name(self):
        """Proxy deletion by realm name

        :id: ef3967e6-d53d-4dec-b74f-c20448d5fc6d

        :expectedresults: Proxy is created and deleted
        """
        name = gen_string('alpha', random.randint(1, 30))
        with self.subTest(name):
            proxy = self._make_proxy({u'name': name})
            self.assertEquals(proxy['name'], name)
            realm = make_realm({'name': gen_string(
                'alpha', random.randint(1, 30)),
                                'realm-proxy-id': proxy['id'],
                                'realm-type': 'Red Hat Identity Management',
                                'locations': proxy['locations']})
            self.assertEquals(len(Realm.list()), 1)
            Realm.delete({'name': realm['name']})
            self.assertEquals(len(Realm.list()), 0)

    @tier1
    def test_positive_create_delete_id(self):
        """Proxy deletion by realm id

        :id: 7c1aca0e-9724-40de-b38f-9189bdae0514

        :expectedresults: Proxy is created and deleted
        """
        name = gen_string('alpha', random.randint(1, 30))
        with self.subTest(name):
            proxy = self._make_proxy({u'name': name})
            realm = make_realm({'name': gen_string(
                'alpha', random.randint(1, 30)),
                                'realm-proxy-id': proxy['id'],
                                'realm-type': 'Active Directory',
                                'locations': proxy['locations']})
            self.assertEquals(len(Realm.list()), 1)
            Realm.delete({'id': realm['id']})
            self.assertEquals(len(Realm.list()), 0)

    @tier1
    def test_positive_realm_info_name(self):
        """Test realm info functionality

        :id: 2e3e92df-61f3-4c6b-98b9-dc9c2f8d140c

        :expectedresults: Realm info information from name is correct
        """
        name = gen_string('alpha', random.randint(1, 30))
        with self.subTest(name):
            proxy = self._make_proxy({u'name': name})
            realm = make_realm({'name': 'info_test',
                                'realm-proxy-id': proxy['id'],
                                'realm-type': 'Red Hat Identity Management',
                                'locations': proxy['locations']})
            info = Realm.info({'name': realm['name']})
            for key in info.keys():
                self.assertEquals(info[key], realm[key])
            Realm.delete({'name': realm['name']})

    @tier1
    def test_positive_realm_info_id(self):
        """Test realm info functionality

        :id: 1ae7b3af-221e-4480-9e93-d05d573456b4

        :expectedresults: Realm info information from ID is correct
        """
        name = gen_string('alpha', random.randint(1, 30))
        with self.subTest(name):
            proxy = self._make_proxy({u'name': name})
            realm = make_realm({'name': 'info_test',
                                'realm-proxy-id': proxy['id'],
                                'realm-type': 'Active Directory',
                                'locations': proxy['locations']})
            info = Realm.info({'id': realm['id']})
            for key in info.keys():
                self.assertEquals(info[key], realm[key])
            self.assertEquals(info, Realm.info({'id': realm['id']}))
            Realm.delete({'id': realm['id']})

    @tier1
    def test_positive_realm_update_name(self):
        """Test updating realm name

        :id: c09e6599-c77a-4290-ac93-311d06e3d860

        :expectedresults: Realm name updated
        """
        name = gen_string('alpha', random.randint(1, 30))
        realm_name1 = "test"
        realm_name2 = "update_test"
        with self.subTest(name):
            proxy = self._make_proxy({u'name': name})
            realm = make_realm({'name': realm_name1,
                                'realm-proxy-id': proxy['id'],
                                'realm-type': 'Active Directory',
                                'locations': proxy['locations']})
            self.assertEquals(realm['name'], realm_name1)
            up = Realm.update({'id': realm['id'], 'new-name': realm_name2})
            self.assertEquals(up[0]['message'], 'Realm [{0}] updated'.format(
                realm_name2))
            realm = Realm.info({'id': realm['id']})
            self.assertEquals(realm['name'], realm_name2)
            Realm.delete({'id': realm['id']})

    @tier1
    def test_positive_realm_update_type(self):
        """Test updating realm type

        :id: 331b1252-1eb0-459a-b751-3a3619c30db9

        :expectedresults: Realm type updated
        """
        name = gen_string('alpha', random.randint(1, 30))
        realm_type1 = 'Active Directory'
        realm_type2 = 'Red Hat Identity Management'
        with self.subTest(name):
            proxy = self._make_proxy({u'name': name})
            realm = make_realm({'name': "realm",
                                'realm-proxy-id': proxy['id'],
                                'realm-type': realm_type1,
                                'locations': proxy['locations']})
            self.assertEquals(realm['realm-type'], realm_type1)
            up = Realm.update({'id': realm['id'], 'realm-type': realm_type2})
            self.assertEquals(up[0]['message'], 'Realm [{0}] updated'.format(
                realm['name']))
            realm = Realm.info({'id': realm['id']})
            self.assertEquals(realm['realm-type'], realm_type2)
            Realm.delete({'id': realm['id']})

    @tier1
    def test_negative_realm_update_invalid_type(self):
        """Test updating realm with an invalid type

        :id: 3097f8e5-9152-4d8d-9991-969bdfc9c4d4

        :expectedresults: Realm is not updated
        """
        name = gen_string('alpha', random.randint(1, 30))
        realm_type1 = 'Red Hat Identity Management'
        realm_type2 = 'invalid'
        with self.subTest(name):
            proxy = self._make_proxy({u'name': name})
            realm = make_realm({'name': "realm",
                                'realm-proxy-id': proxy['id'],
                                'realm-type': realm_type1,
                                'locations': proxy['locations']})
            with self.assertRaises(CLIReturnCodeError):
                Realm.update({'id': realm['id'], 'realm-type': realm_type2})
            Realm.delete({'id': realm['id']})

    @tier1
    def test_negative_create_name_only(self):
        """Create a realm with just a name parameter

        :id: 5606279f-0707-4d36-a307-b204ebb981ad

        :expectedresults: Realm creation fails, requires proxy_id and type
        """
        with self.assertRaises(CLIFactoryError):
            make_realm({'name': 'test'})

    @tier1
    def test_negative_create_invalid_id(self):
        """Create a realm with an invalid proxy id

        :id: 916bd1fb-4649-469c-b511-b0b07301a990

        :expectedresults: Realm creation fails, proxy_id must be numeric
        """
        with self.assertRaises(CLIFactoryError):
            make_realm({'name': 'test', 'realm-proxy-id': 'invalid_id',
                        'realm-type': 'Red Hat Identity Management'})

    @tier1
    def test_negative_create_invalid_realm_type(self):
        """Create a realm with an invalid type

        :id: 423a0969-9311-48d2-9220-040a42159a89

        :expectedresults: Realm creation fails, type must be in list
            e.g. Red Hat Identity Management or Active Directory
        """
        with self.assertRaises(CLIFactoryError):
            make_realm({'name': 'test', 'realm-proxy-id': '1',
                        'realm-type': 'invalid_type'})

    @tier1
    def test_negative_create_invalid_location(self):
        """Create a realm with an invalid location

        :id: 95335c3a-413f-4156-b727-91b525738171

        :expectedresults: Realm creation fails, location not found

        """
        with self.assertRaises(CLIFactoryError):
            make_realm({'name': 'test', 'realm-proxy-id': '1',
                        'locations': 'Raleigh, NC',
                        'realm-type': 'invalid_type'})

    @tier1
    def test_negative_create_invalid_organization(self):
        """Create a realm with an invalid type

        :id: c0ffbc6d-a2da-484b-9627-5454687a3abb

        :expectedresults: Realm creation fails, organization not found
        """
        with self.assertRaises(CLIFactoryError):
            make_realm({'name': 'test', 'realm-proxy-id': '1',
                        'organizations': 'Red Hat',
                        'realm-type': 'invalid_type'})

    @tier1
    def test_negative_delete_nonexistent_realm_name(self):
        """Delete a realm with a name that does not exist

        :id: 616db509-9643-4817-ba6b-f05cdb1cecb0

        :expectedresults: Realm not found
        """
        with self.assertRaises(CLIReturnCodeError):
            Realm.delete({'name': 'dne'})

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
            Realm.info({'name': 'dne'})

    @tier1
    def test_negative_info_nonexistent_realm_id(self):
        """Get info for a realm with an id that does not exists

        :id: db8382eb-6d0b-4d6a-a9bf-38a462389f7b

        :expectedresults: Realm not found
        """
        with self.assertRaises(CLIReturnCodeError):
            Realm.info({'id': 0})

    @tier1
    def test_negative_update_nonexistent_realm_name(self):
        """Update realm with a name that does not exists

        :id: 912bf1b9-5662-4f49-839b-f7e7085baf27

        :expectedresults: Realm not found
        """
        with self.assertRaises(CLIReturnCodeError):
            Realm.update({'name': 'dne', 'new-name': 'test'})

    @tier1
    def test_negative_update_nonexistent_realm_id(self):
        """Update realm with an id that does not exists

        :id: aa3fa540-663c-48ce-ac06-61c6c1ad9542

        :expectedresults: Realm not found
        """
        with self.assertRaises(CLIReturnCodeError):
            Realm.update({'id': 0, 'locations': make_location()})
