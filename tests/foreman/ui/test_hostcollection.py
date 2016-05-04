# -*- encoding: utf-8 -*-
"""Test class for Host Collection UI"""

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

        @Feature: Host Collection - Positive Create

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

        @Feature: Host Collection - Positive Create

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

        @Feature: Host Collection - Positive Create

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

        @Feature: Host Collection - Positive Negative

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

        @Feature: Host Collections - Negative Create

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

        @Feature: Host Collection - Positive Update

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

        @Feature: Host Collection - Positive Update

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

        @Feature: Host Collection - Positive Update

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

        @Feature: Host Collection - Positive Update

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

        @Feature: Host Collection - Negative Update

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

        @Feature: Host Collection - Negative Update

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

        @Feature: Host Collection - Positive Delete

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

        @Feature: Host Collection - Positive Copy

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

        @Feature: Host Collection - Negative Copy

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

        @Feature: Host Collection - Host

        @Assert: Host is added to Host Collection successfully
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

        @Feature: Host Collection - Host Limit

        @Steps:
        1. Create Host Collection entity that can contain only one Host (using
        Host Limit field)
        2. Create Host and add it to Host Collection. Check that it was added
        successfully
        3. Create one more Host and try to add it to Host Collection
        4. Check that expected error is shown

        @Assert: Second host is not added to Host Collection and appropriate
        error is shown
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
