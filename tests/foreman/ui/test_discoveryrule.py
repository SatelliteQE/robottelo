# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery Rules"""
from fauxfactory import gen_string
from nailgun import entities
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import run_only_on, tier1
from robottelo.test import UITestCase
from robottelo.ui.factory import make_discoveryrule
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class DiscoveryRuleTestCase(UITestCase):
    """Implements Foreman discovery Rules in UI."""

    @classmethod
    def setUpClass(cls):
        """Display all the discovery rules on the same page"""
        super(DiscoveryRuleTestCase, cls).setUpClass()
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

        super(DiscoveryRuleTestCase, cls).tearDownClass()

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create Discovery Rule using different names

        @Feature: Foreman Discovery

        @Assert: Rule should be successfully created
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_discoveryrule(session, name=name,
                                       hostgroup=self.host_group.name)
                    self.assertIsNotNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create Discovery Rule with invalid names

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
    @tier1
    def test_negative_create_with_limit(self):
        """Create Discovery Rule with invalid host limit

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
    @tier1
    def test_negative_create_with_same_name(self):
        """Create Discovery Rule with name that already exists

        @Feature: Foreman Discovery

        @Assert: Error should be raised and rule should not be created
        """
        name = gen_string('alpha')
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
    @tier1
    def test_negative_create_with_invalid_priority(self):
        """Create Discovery Rule with invalid priority

        @Feature: Foreman Discovery

        @Assert: Error should be raised and rule should not be created
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.host_group.name,
                               priority=gen_string('alpha', 6))
            self.assertIsNotNone(self.discoveryrules.wait_until_element(
                common_locators['haserror']
            ))
            self.assertIsNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_disable(self):
        """Disable Discovery Rule while creation

        @Feature: Foreman Discovery

        @Assert: Rule should be disabled
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.host_group.name, enable=True)
            self.assertIsNotNone(self.discoveryrules.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete Discovery Rule

        @Feature: Foreman Discovery

        @Assert: Rule should be successfully created
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_discoveryrule(session, name=name,
                                       hostgroup=self.host_group.name)
                    self.assertIsNotNone(self.discoveryrules.search(name))
                    self.discoveryrules.delete(name)

    @run_only_on('sat')
    @tier1
    def test_positive_update_name(self):
        """Update discovery rule name

        @Feature: Discovery Rule - Update

        @Assert: Rule name is updated
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.host_group.name)
            self.assertIsNotNone(self.discoveryrules.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.discoveryrules.update(name=name, new_name=new_name)
                    self.assertIsNotNone(self.discoveryrules.search(new_name))
                    name = new_name  # for next iteration
