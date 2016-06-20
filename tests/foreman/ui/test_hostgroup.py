# -*- encoding: utf-8 -*-
"""Test class for Host Group UI

@Requirement: Hostgroup

@CaseAutomation: Automated

@CaseLevel: Acceptance

@CaseComponent: UI

@TestType: Functional

@CaseImportance: High

@Upstream: No
"""

from fauxfactory import gen_string
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import run_only_on, tier1
from robottelo.test import UITestCase
from robottelo.ui.factory import make_hostgroup
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class HostgroupTestCase(UITestCase):
    """Implements HostGroup tests from UI"""

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create new hostgroup

        @id: 8bcf45e5-9e7f-4050-9de6-a90350b70006

        @Assert: Hostgroup is created
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=4):
                with self.subTest(name):
                    make_hostgroup(session, name=name)
                    self.assertIsNotNone(self.hostgroup.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create new hostgroup with invalid names

        @id: a0232740-ae9f-44ce-9f3d-bafc8f1b05cb

        @Assert: Hostgroup is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_hostgroup(session, name=name)
                    self.assertIsNotNone(self.hostgroup.wait_until_element
                                         (common_locators['name_haserror']))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_same_name(self):
        """Create new hostgroup with same name

        @id: 237b684d-3b55-444a-be00-a9825952bb53

        @Assert: Hostgroup is not created
        """
        name = gen_string('utf8')
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.wait_until_element
                                 (common_locators['name_haserror']))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete a hostgroup

        @id: f118532b-ca9b-4bf4-b53b-9573abcb347a

        @Assert: Hostgroup is deleted
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=4):
                with self.subTest(name):
                    make_hostgroup(session, name=name)
                    self.hostgroup.delete(name)

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """Update hostgroup with a new name

        @id: 7c8de1b8-aced-44f0-88a0-dc9e6b83bf7f

        @Assert: Hostgroup is updated
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_hostgroup(session, name=name)
            self.assertIsNotNone(self.hostgroup.search(name))
            for new_name in generate_strings_list(length=4):
                with self.subTest(new_name):
                    self.hostgroup.update(name, new_name=new_name)
                    self.assertIsNotNone(self.hostgroup.search(new_name))
                    name = new_name  # for next iteration
