# -*- encoding: utf-8 -*-
"""Test class for Host Collection UI

@Requirement: Hostcollection

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.api.utils import promote
from robottelo.cli.factory import make_content_host
from robottelo.datafactory import (
    invalid_names_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import (
    skip_if_bug_open,
    tier1,
    tier3,
)
from robottelo.test import UITestCase
from robottelo.ui.base import UIError
from robottelo.ui.factory import make_host_collection
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class HostCollectionTestCase(UITestCase):
    """Implements Host Collection tests in UI"""

    @classmethod
    def setUpClass(cls):
        super(HostCollectionTestCase, cls).setUpClass()
        cls.organization = entities.Organization().create()

    @tier1
    def test_positive_create_with_name(self):
        """Create Host Collection for all name variations

        @id: 267bd784-1ef7-4270-a264-6f8659e239fd

        @Assert: Host Collection is created
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_host_collection(
                        session, org=self.organization.name, name=name)
                    self.assertIsNotNone(self.hostcollection.search(name))

    @tier1
    def test_positive_create_with_description(self):
        """Create Host Collection with valid description

        @id: 830ff39e-0d4c-4368-bc47-12b060a09410

        @Assert: Host Collection is created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session,
                name=name,
                org=self.organization.name,
                description=gen_string('alphanumeric'),
            )
            self.assertIsNotNone(self.hostcollection.search(name))

    @tier1
    def test_positive_create_with_limit(self):
        """Create Host Collection with finite content hosts limit

        @id: 9983b61d-f820-4b60-ae5e-a45925f2dcf0

        @Assert: Host Collection is created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name, limit='10')
            self.assertIsNotNone(self.hostcollection.search(name))

    @tier1
    def test_negative_create_with_name(self):
        """Create Host Collections with invalid name

        @id: 04e36c46-7577-4308-b9bb-4ec74549d9d3

        @Assert: Host Collection is not created and appropriate error message
        thrown
        """
        with Session(self.browser) as session:
            for name in invalid_values_list('ui'):
                with self.subTest(name):
                    make_host_collection(
                        session, org=self.organization.name, name=name)
                    self.assertIsNotNone(
                        self.hostcollection.wait_until_element(
                            common_locators['common_invalid'])
                    )

    @skip_if_bug_open('bugzilla', 1300350)
    @tier1
    def test_negative_create_with_invalid_limit(self):
        """Create Host Collections with invalid Content Host Limit value. Both
        with too long numbers and using letters.

        @id: c15b3540-809e-4339-ad5f-1ab488244299

        @Assert: Host Collection is not created. Appropriate error shown.
        """
        with Session(self.browser) as session:
            for limit in invalid_names_list():
                with self.subTest(limit):
                    make_host_collection(
                        session,
                        name=gen_string('alpha'),
                        org=self.organization.name,
                        limit=limit,
                    )
                    self.assertIsNotNone(
                        self.hostcollection.wait_until_element(
                            common_locators['invalid_limit'])
                    )

    @tier1
    def test_positive_update_name(self):
        """Update existing Host Collection name

        @id: 9df33661-7a9c-40d9-8f2c-52e5ed21c156

        @Assert: Host Collection is updated
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.hostcollection.update(name, new_name=new_name)
                    self.assertIsNotNone(self.hostcollection.search(new_name))
                    name = new_name

    @tier1
    def test_positive_update_description(self):
        """Update existing Host Collection entity description

        @id: 5ef92657-489f-46a2-9b3a-e40322ca86d8

        @Assert: Host Collection is updated
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session,
                name=name,
                org=self.organization.name,
                description=gen_string('alpha'),
            )
            self.assertIsNotNone(self.hostcollection.search(name))
            for new_desc in valid_data_list():
                with self.subTest(new_desc):
                    self.hostcollection.update(name, description=new_desc)
                    self.assertIsNotNone(
                        self.hostcollection.wait_until_element(
                            common_locators['alert.success_sub_form'])
                    )
                    self.assertTrue(self.hostcollection.validate_field_value(
                        name, 'description', new_desc))

    @tier1
    def test_positive_update_limit(self):
        """Update Content Host limit from Unlimited to a finite number

        @id: 6f5015c4-06c9-4873-806e-5f9d39c9d8a8

        @Assert: Host Collection is updated
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            self.hostcollection.update(name, limit='25')
            self.assertIsNotNone(self.hostcollection.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.assertTrue(self.hostcollection.validate_field_value(
                name, 'limit', '25'))

    @tier1
    def test_positive_update_limit_to_unlimited(self):
        """Update Content Host limit from definite number to Unlimited

        @id: 823acd9e-1259-47b6-8236-7547ef3fff98

        @Assert: Host Collection is updated
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name, limit='15')
            self.assertIsNotNone(self.hostcollection.search(name))
            self.hostcollection.update(name, limit='Unlimited')
            self.assertIsNotNone(self.hostcollection.wait_until_element(
                common_locators['alert.success_sub_form']))
            self.assertTrue(self.hostcollection.validate_field_value(
                name, 'limit', 'Unlimited'))

    @tier1
    def test_negative_update_name(self):
        """Update existing Host Collection entity name with invalid value

        @id: 7af999e8-5189-45c0-a92d-8c05b03f556a

        @Assert: Host Collection is not updated.  Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.hostcollection.update(name, new_name=new_name)
                    self.assertIsNotNone(
                        self.hostcollection.wait_until_element(
                            common_locators['alert.error_sub_form'])
                    )

    @tier1
    def test_negative_update_limit(self):
        """Update Host Collection with invalid Content Host Limit

        @id: 3f3749f9-cf52-4897-993f-804def785510

        @Assert: Host Collection is not updated.  Appropriate error shown.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for limit in ' ', -1, 'text', '0':
                with self.subTest(limit):
                    with self.assertRaises(ValueError):
                        self.hostcollection.update(name, limit=limit)

    @tier1
    def test_positive_delete(self):
        """Create Host Collection and delete it for all variations of name

        @id: 978a985c-29f4-4b1f-8c68-8cd412af21e6

        @Assert: Host Collection is deleted
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_host_collection(
                        session, name=name, org=self.organization.name)
                    self.assertIsNotNone(self.hostcollection.search(name))
                    self.hostcollection.delete(name)

    @tier1
    def test_positive_copy(self):
        """Create Host Collection and copy it

        @id: af8d968c-8241-40dc-b92c-81965f470191

        @Assert: Host Collection copy exists
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.hostcollection.copy(name, new_name)
                    self.assertIsNotNone(
                        self.hostcollection.search(new_name))

    @tier1
    def test_negative_copy(self):
        """Create Host Collection and copy it. Use invalid values for copy name

        @id: 99d47520-c09a-4fbc-8e53-a4e889af0187

        @Assert: Host Collection copy does not exist
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.hostcollection.copy(name, new_name)
                    self.assertIsNotNone(
                        self.hostcollection.wait_until_element(
                            common_locators['alert.error_sub_form'])
                    )

    @tier3
    def test_positive_add_host(self):
        """Check if host can be added to Host Collection

        @id: 80824c9f-15a1-4f76-b7ac-7d9ca9f6ed9e

        @Assert: Host is added to Host Collection successfully

        @CaseLevel: System
        """
        name = gen_string('alpha')
        cv = entities.ContentView(organization=self.organization).create()
        lce = entities.LifecycleEnvironment(
            organization=self.organization).create()
        cv.publish()
        promote(cv.read().version[0], lce.id)
        new_system = make_content_host({
            u'content-view-id': cv.id,
            u'lifecycle-environment-id': lce.id,
            u'name': gen_string('alpha'),
            u'organization-id': self.organization.id,
        })
        with Session(self.browser) as session:
            make_host_collection(
                session, org=self.organization.name, name=name)
            self.hostcollection.add_host(name, new_system['name'])

    @tier3
    def test_negative_hosts_limit(self):
        """Check that Host limit actually limits usage

        @id: 57b70977-2110-47d9-be3b-461ad15c70c7

        @Steps:
        1. Create Host Collection entity that can contain only one Host (using
        Host Limit field)
        2. Create Host and add it to Host Collection. Check that it was added
        successfully
        3. Create one more Host and try to add it to Host Collection
        4. Check that expected error is shown

        @Assert: Second host is not added to Host Collection and appropriate
        error is shown

        @CaseLevel: System
        """
        name = gen_string('alpha')
        org = entities.Organization().create()
        cv = entities.ContentView(organization=org).create()
        lce = entities.LifecycleEnvironment(organization=org).create()
        cv.publish()
        promote(cv.read().version[0], lce.id)
        new_systems = [
            make_content_host({
                u'content-view-id': cv.id,
                u'lifecycle-environment-id': lce.id,
                u'name': gen_string('alpha'),
                u'organization-id': org.id,
            })['name']
            for _ in range(2)
        ]
        with Session(self.browser) as session:
            make_host_collection(
                session, org=org.name, name=name, limit='1')
            self.hostcollection.add_host(name, new_systems[0])
            with self.assertRaises(UIError):
                self.hostcollection.add_host(name, new_systems[1])
            self.assertIsNotNone(self.hostcollection.wait_until_element(
                common_locators['alert.error_sub_form']))
