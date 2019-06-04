# -*- encoding: utf-8 -*-
"""Test class for Organization UI

:Requirement: Organization

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
    filtered_datapoint,
    generate_strings_list,
    invalid_names_list,
    invalid_values_list,
)
from robottelo.decorators import (
    skip_if_bug_open,
    stubbed,
    tier1,
    tier2,
    upgrade
)
from robottelo.test import UITestCase
from robottelo.ui.factory import make_org
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


@filtered_datapoint
def valid_labels():
    """Returns a list of valid labels"""
    return [
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
    ]


@filtered_datapoint
def valid_users():
    """Returns a list of valid users"""
    return [
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
        gen_string('utf8'),
        gen_string('latin1'),
        # Note: HTML username is invalid as per the UI msg.
    ]


@filtered_datapoint
def valid_env_names():
    """Returns a list of valid environment names"""
    return [
        gen_string('alpha'),
        gen_string('numeric'),
        gen_string('alphanumeric'),
    ]


class OrganizationTestCase(UITestCase):
    """Implements Organization tests in UI"""

    @tier1
    def test_positive_search_autocomplete(self):
        """Search for an organization can be auto-completed by partial
        name

        :id: f3c492ab-46fb-4b1d-b5d5-29a82385d681

        :expectedresults: Auto search for created organization works as
            intended

        :CaseImportance: Critical
        """
        org_name = gen_string('alpha')
        part_string = org_name[:3]
        with Session(self) as session:
            page = session.nav.go_to_org
            make_org(session, org_name=org_name)
            auto_search = self.org.auto_complete_search(
                page, locators['org.org_name'], part_string, org_name,
                search_key='name')
            self.assertIsNotNone(auto_search)

    @tier1
    def test_positive_search_scoped(self):
        """Test scoped search functionality for organization by label

        :id: 18ad9aad-335a-414e-843e-e1c05ec6bcbb

        :customerscenario: true

        :expectedresults: Proper organization is found

        :BZ: 1259374

        :CaseImportance: Critical
        """
        org_name = gen_string('alpha')
        label = gen_string('alpha')
        with Session(self) as session:
            make_org(session, org_name=org_name, label=label)
            for query in [
                'label = {}'.format(label),
                'label ~ {}'.format(label[:-5]),
                'label ^ "{}"'.format(label),
            ]:
                self.assertIsNotNone(
                    self.org.search(org_name, _raw_query=query))

    @tier1
    def test_positive_create_with_name(self):
        """Create organization with valid name only.

        :id: bb5c6400-e837-4e3b-add9-bab2c0b826c9

        :expectedresults: Organization is created, label is auto-generated

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))

    @tier1
    def test_positive_create_with_unmatched_name_label(self):
        """Create organization with valid unmatching name and label only

        :id: 82954640-05c2-4d6c-a293-dc4aa3e5611b

        :expectedresults: organization is created, label does not match name

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for label in valid_labels():
                with self.subTest(label):
                    org_name = gen_string('alphanumeric')
                    make_org(
                        session, org_name=org_name, label=label)
                    self.org.search_and_click(org_name)
                    name = session.nav.wait_until_element(
                        locators['org.name']).get_attribute('value')
                    label = session.nav.wait_until_element(
                        locators['org.label']).get_attribute('value')
                    self.assertNotEqual(name, label)

    @tier1
    def test_positive_create_with_same_name_and_label(self):
        """Create organization with valid matching name and label only.

        :id: 73befc8c-bf96-48b7-8315-34f0cfef9382

        :expectedresults: organization is created, label matches name

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for item in valid_labels():
                with self.subTest(item):
                    make_org(session, org_name=item, label=item)
                    self.org.search_and_click(item)
                    name = self.org.wait_until_element(
                        locators['org.name']).get_attribute('value')
                    label = self.org.wait_until_element(
                        locators['org.label']).get_attribute('value')
                    self.assertEqual(name, label)

    @skip_if_bug_open('bugzilla', 1079482)
    @tier1
    def test_positive_create_with_auto_populated_label(self):
        """Create organization with valid name. Check that organization
        label is auto-populated

        :id: 29793945-c553-4a6e-881f-cdcde373aa62

        :expectedresults: organization is created, label is auto-generated

        :BZ: 1079482

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.search_and_click(org_name)
                    label = session.nav.wait_until_element(
                        locators['org.label'])
                    label_value = label.get_attribute('value')
                    self.assertIsNotNone(label_value)

    @tier1
    def test_negative_create(self):
        """Try to create organization and use whitespace, blank, tab
        symbol or too long string of different types as its name value

        :id: e69ab8c1-e53f-41fa-a84f-290c6c152484

        :expectedresults: organization is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for org_name in invalid_values_list(interface='ui'):
                with self.subTest(org_name):
                    make_org(session, org_name=org_name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @tier1
    def test_negative_create_with_same_name(self):
        """Create organization with valid names, then create a new one
        with same names.

        :id: d7fd91aa-1a0e-4403-8dea-cc03cbb93070

        :expectedresults: organization is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    make_org(session, org_name=org_name)
                    self.assertIsNotNone(self.org.search(org_name))
                    self.org.create(org_name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Create organization with valid values then delete it.

        :id: 6b69d505-56b1-4d7d-bf2a-8762d5184ca8

        :expectedresults: Organization is deleted successfully

        :CaseImportance: Critical
        """
        with Session(self):
            for org_name in generate_strings_list():
                with self.subTest(org_name):
                    entities.Organization(name=org_name).create()
                    self.org.delete(org_name, dropdown_present=True)

    @tier1
    def test_positive_update_name(self):
        """Create organization with valid values then update its name.

        :id: 776f5268-4f05-4cfc-a1e9-339a3e224677

        :expectedresults: Organization name is updated successfully

        :CaseImportance: Critical
        """
        org_name = gen_string('alpha')
        with Session(self) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    self.org.update(org_name, new_name=new_name)
                    self.assertIsNotNone(self.org.search(new_name))
                    org_name = new_name  # for next iteration

    @tier1
    def test_negative_update(self):
        """Create organization with valid values then try to update it
        using incorrect name values

        :id: 1467a04e-ebd6-4106-94b1-841a4f0ddecb

        :expectedresults: Organization name is not updated

        :CaseImportance: Critical
        """
        org_name = gen_string('alpha')
        with Session(self) as session:
            make_org(session, org_name=org_name)
            self.assertIsNotNone(self.org.search(org_name))
            for new_name in invalid_names_list():
                with self.subTest(new_name):
                    self.org.update(org_name, new_name=new_name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @stubbed()
    @tier2
    def test_positive_create_with_smartproxy(self):
        """Add a smart proxy during org creation.

        :id: 7ad6f610-91ca-4f1f-b9c4-8ce82f50ea9e

        :expectedresults: smartproxy is added

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """

    @stubbed()
    @tier2
    def test_positive_update_smartproxy(self):
        """Add and Remove smartproxy by using organization name and smartproxy
        name

        :id: 25bc6334-de59-462c-824a-51d615d9fdd0

        :expectedresults: smartproxy is added then removed

        :CaseAutomation: notautomated

        :CaseLevel: Integration
        """
