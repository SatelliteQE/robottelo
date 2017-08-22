# -*- encoding: utf-8 -*-
"""Test class for Architecture UI

:Requirement: Architecture

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
    invalid_values_list,
)
from robottelo.decorators import run_only_on, tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.factory import make_arch
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@filtered_datapoint
def valid_arch_os_names():
    """Returns a list of arch/os names for creation tests"""
    return [
        {u'name': gen_string('alpha'), u'os_name': gen_string('alpha')},
        {u'name': gen_string('html'), u'os_name': gen_string('html')},
        {u'name': gen_string('utf8'), u'os_name': gen_string('utf8')},
        {u'name': gen_string('alphanumeric'),
         u'os_name': gen_string('alphanumeric')}
    ]


class ArchitectureTestCase(UITestCase):
    """Implements Architecture tests from UI"""

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_os(self):
        """Create a new Architecture with OS

        :id: 6c386230-2285-4f41-a3a5-6a17ae844f80

        :expectedresults: Architecture is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for test_data in valid_arch_os_names():
                with self.subTest(test_data):
                    entities.OperatingSystem(
                        name=test_data['os_name']).create()
                    make_arch(
                        session,
                        name=test_data['name'],
                        os_names=[test_data['os_name']]
                    )
                    self.assertIsNotNone(
                        self.architecture.search(test_data['name']))

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create a new Architecture with different data

        :id: 0ac5f63b-b296-425b-8bb2-e0fe32d394c5

        :expectedresults: Architecture is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_arch(session, name=name)
                    self.assertIsNotNone(self.architecture.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Try to create architecture and use whitespace, blank, tab
        symbol or too long string of different types as its name value

        :id: f4b8ed72-f20b-4f5d-bf0a-3475a6124f3a

        :expectedresults: Architecture is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for invalid_name in invalid_values_list(interface='ui'):
                with self.subTest(invalid_name):
                    make_arch(session, name=invalid_name)
                    self.assertIsNotNone(self.architecture.wait_until_element(
                        common_locators['name_haserror']))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Create a new Architecture with same name

        :id: 4000674e-7b39-4958-8992-1363b25b2cd6

        :expectedresults: Architecture is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in generate_strings_list():
                with self.subTest(name):
                    make_arch(session, name=name)
                    self.assertIsNotNone(self.architecture.search(name))
                    make_arch(session, name=name)
                    self.assertIsNotNone(self.architecture.wait_until_element(
                        common_locators['name_haserror']))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete an existing Architecture

        :id: f58af0ba-45c8-456c-abe3-8aaf48055c23

        :expectedresults: Architecture is deleted

        :CaseImportance: Critical
        """
        os = entities.OperatingSystem(name=gen_string('alpha')).create()
        with Session(self):
            for name in generate_strings_list():
                with self.subTest(name):
                    entities.Architecture(
                        name=name, operatingsystem=[os]).create()
                    self.architecture.delete(name)

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_update_name_and_os(self):
        """Update Architecture with new name and OS

        :id: cbb2e8fc-1dde-42c4-aab0-479bd16fb5ec

        :expectedresults: Architecture is updated

        :CaseImportance: Critical
        """
        old_name = gen_string('alpha')
        os_name = gen_string('alpha')
        entities.OperatingSystem(name=os_name).create()
        with Session(self) as session:
            make_arch(session, name=old_name)
            self.assertIsNotNone(self.architecture.search(old_name))
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    self.architecture.update(
                        old_name, new_name, new_os_names=[os_name])
                    self.assertIsNotNone(self.architecture.search(new_name))
                    old_name = new_name  # for next iteration
