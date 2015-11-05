# -*- encoding: utf-8 -*-
# pylint: disable=invalid-name
"""Test class for Foreman Discovery Rules"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import generate_strings_list, invalid_values_list
from robottelo.decorators import run_only_on
from robottelo.test import UITestCase
from robottelo.ui.factory import make_discoveryrule
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class DiscoveryRules(UITestCase):
    """Implements Foreman discovery Rules in UI."""

    @classmethod
    def setUpClass(cls):
        """Display all the discovery rules on the same page"""
        super(DiscoveryRules, cls).setUpClass()
        cls.per_page = entities.Setting().search(
            query={'search': 'name="entries_per_page"'})[0]
        cls.saved_per_page = str(cls.per_page.value)
        cls.per_page.value = '100000'
        cls.per_page.update({'value'})

        cls.host_group = entities.HostGroup().create()

    @classmethod
    def tearDownClass(cls):
        """Restore previous 'entries_per_page' value"""
        cls.per_page.value = cls.saved_per_page
        cls.per_page.update({'value'})

        super(DiscoveryRules, cls).tearDownClass()

    @run_only_on('sat')
    def test_positive_create_discovery_rule_1(self):
        """@Test: Create Discovery Rule

        @Feature: Foreman Discovery

        @Assert: Rule should be successfully created

        """
        with Session(self.browser) as session:
            for name in generate_strings_list(len1=8):
                with self.subTest(name):
                    make_discoveryrule(session, name=name,
                                       hostgroup=self.host_group.name)
                    self.assertIsNotNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    def test_positive_create_discovery_rule_2(self):
        """@Test: Create Discovery Rule with 255 characters in name

        @Feature: Foreman Discovery

        @Assert: Rule should be successfully created

        """
        name = gen_string('alpha', 255)
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.host_group.name)
            self.assertIsNotNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    def test_negative_create_discovery_rule_1(self):
        """@Test: Create Discovery Rule with invalid names

        @Feature: Foreman Discovery

        @Assert: Error should be raised and rule should not be created

        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_discoveryrule(session, name=name,
                                       hostgroup=self.host_group.name)
                    self.assertIsNotNone(
                        self.discoveryrules.wait_until_element(
                            common_locators['name_haserror'])
                    )
                    self.assertIsNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    def test_negative_create_discovery_rule_2(self):
        """@Test: Create Discovery Rule with invalid host limit

        @Feature: Foreman Discovery

        @Assert: Error should be raised and rule should not be created

        """
        name = gen_string("alpha", 6)
        with Session(self.browser) as session:
            for limit in '-1', gen_string("alpha", 6):
                with self.subTest(limit):
                    make_discoveryrule(session, name=name, host_limit=limit,
                                       hostgroup=self.host_group.name)
                    self.assertIsNotNone(
                        self.discoveryrules.wait_until_element(
                            common_locators['haserror'])
                    )
                    self.assertIsNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    def test_negative_create_discovery_rule_3(self):
        """@Test: Create Discovery Rule with name that already exists

        @Feature: Foreman Discovery

        @Assert: Error should be raised and rule should not be created

        """
        name = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.host_group.name)
            self.assertIsNotNone(self.discoveryrules.search(name))
            make_discoveryrule(session, name=name,
                               hostgroup=self.host_group.name)
            self.assertIsNotNone(self.discoveryrules.wait_until_element(
                common_locators['name_haserror']
            ))

    @run_only_on('sat')
    def test_negative_create_discovery_rule_4(self):
        """@Test: Create Discovery Rule with invalid priority

        @Feature: Foreman Discovery

        @Assert: Error should be raised and rule should not be created

        """
        name = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.host_group.name,
                               priority=gen_string('alpha', 6))
            self.assertIsNotNone(self.discoveryrules.wait_until_element(
                common_locators['haserror']
            ))
            self.assertIsNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    def test_disable_discovery_rule_1(self):
        """@Test: Disable Discovery Rule while creation

        @Feature: Foreman Discovery

        @Assert: Rule should be disabled

        """
        name = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.host_group.name, enable=True)
            self.assertIsNotNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    def test_delete_discovery_rule_1(self):
        """@Test: Delete Discovery Rule

        @Feature: Foreman Discovery

        @Assert: Rule should be successfully created

        """
        with Session(self.browser) as session:
            for name in generate_strings_list(len1=8):
                with self.subTest(name):
                    make_discoveryrule(session, name=name,
                                       hostgroup=self.host_group.name)
                    self.assertIsNotNone(self.discoveryrules.search(name))
                    self.discoveryrules.delete(name)
                    self.assertIsNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    def test_update_discovery_rule_1(self):
        """@Test: Update discovery rule name

        @Feature: Discovery Rule - Update

        @Assert: Rule name is updated

        """
        name = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.host_group.name)
            self.assertIsNotNone(self.discoveryrules.search(name))
            for new_name in generate_strings_list(len1=8):
                with self.subTest(new_name):
                    self.discoveryrules.update(name=name, new_name=new_name)
                    self.assertIsNotNone(self.discoveryrules.search(new_name))
                    name = new_name  # for next iteration
