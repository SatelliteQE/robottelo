# -*- encoding: utf-8 -*-
"""Test class for Host Collection UI

:Requirement: Hostcollection

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import (
    invalid_names_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import (
    run_in_one_thread,
    skip_if_bug_open,
    stubbed,
    tier1,
    upgrade
)
from robottelo.test import UITestCase
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

        :id: 267bd784-1ef7-4270-a264-6f8659e239fd

        :expectedresults: Host Collection is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_host_collection(
                        session, org=self.organization.name, name=name)
                    self.assertIsNotNone(self.hostcollection.search(name))

    @tier1
    def test_positive_create_with_description(self):
        """Create Host Collection with valid description

        :id: 830ff39e-0d4c-4368-bc47-12b060a09410

        :expectedresults: Host Collection is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
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

        :id: 9983b61d-f820-4b60-ae5e-a45925f2dcf0

        :expectedresults: Host Collection is created

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_host_collection(
                session, name=name, org=self.organization.name, limit='10')
            self.assertIsNotNone(self.hostcollection.search(name))

    @tier1
    def test_negative_create_with_name(self):
        """Create Host Collections with invalid name

        :id: 04e36c46-7577-4308-b9bb-4ec74549d9d3

        :expectedresults: Host Collection is not created and appropriate error
            message thrown

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :id: c15b3540-809e-4339-ad5f-1ab488244299

        :expectedresults: Host Collection is not created. Appropriate error
            shown.

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :id: 9df33661-7a9c-40d9-8f2c-52e5ed21c156

        :expectedresults: Host Collection is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
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

        :id: 5ef92657-489f-46a2-9b3a-e40322ca86d8

        :expectedresults: Host Collection is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
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

        :id: 6f5015c4-06c9-4873-806e-5f9d39c9d8a8

        :expectedresults: Host Collection is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
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

        :id: 823acd9e-1259-47b6-8236-7547ef3fff98

        :expectedresults: Host Collection is updated

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
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

        :id: 7af999e8-5189-45c0-a92d-8c05b03f556a

        :expectedresults: Host Collection is not updated.  Appropriate error
            shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
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

        :id: 3f3749f9-cf52-4897-993f-804def785510

        :expectedresults: Host Collection is not updated.  Appropriate error
            shown.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for limit in ' ', -1, 'text', '0':
                with self.subTest(limit):
                    with self.assertRaises(ValueError):
                        self.hostcollection.update(name, limit=limit)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create Host Collection and delete it for all variations of name

        :id: 978a985c-29f4-4b1f-8c68-8cd412af21e6

        :expectedresults: Host Collection is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_host_collection(
                        session, name=name, org=self.organization.name)
                    self.assertIsNotNone(self.hostcollection.search(name))
                    self.hostcollection.delete(name)

    @tier1
    def test_positive_copy(self):
        """Create Host Collection and copy it

        :id: af8d968c-8241-40dc-b92c-81965f470191

        :expectedresults: Host Collection copy exists

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_host_collection(
                session, name=name, org=self.organization.name)
            self.assertIsNotNone(self.hostcollection.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.hostcollection.copy(name, new_name)
                    self.assertIsNotNone(
                        self.hostcollection.search(new_name))

    @skip_if_bug_open('bugzilla', 1461016)
    @tier1
    def test_negative_copy(self):
        """Create Host Collection and copy it. Use invalid values for copy name

        :id: 99d47520-c09a-4fbc-8e53-a4e889af0187

        :expectedresults: Host Collection copy does not exist

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
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


@run_in_one_thread
class HostCollectionPackageManagementTest(UITestCase):
    """Implements Host Collection package management related tests in UI"""

    @tier1
    @stubbed()
    @upgrade
    def test_positive_add_subscription(self):
        """Try to add a subscription to a host collection

        :id: e705b949-0c3c-4bb5-aab8-c7b3fa3c0228

        :steps:

            1. Create a new or use an existing subscription
            2. Add the subscription to the host collection

        :expectedresults: The subscription was added to the host collection

        :CaseImportance: Critical
        """

    @tier1
    @stubbed()
    def test_positive_remove_subscription(self):
        """Try to remove a subscription from a host collection

        :id: 1c380df4-abee-46f4-8843-5d9e6eacac41

        :steps:

            1. Create a new or use an existing subscription
            2. Add the subscription to the host collection
            3. Remove the subscription from the host collection

        :expectedresults: The subscription was added to the host collection

        :CaseImportance: Critical
        """
