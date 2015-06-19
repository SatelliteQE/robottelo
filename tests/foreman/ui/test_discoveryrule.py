# -*- encoding: utf-8 -*-
"""Test class for Foreman Discovery Rules"""
from ddt import ddt
from fauxfactory import gen_string
from nailgun import entities
from robottelo.common.decorators import data, run_only_on
from robottelo.common.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_discoveryrule
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class DiscoveryRules(UITestCase):
    """Implements Foreman discovery Rules in UI."""
    @classmethod
    def setUpClass(cls):  # noqa
        org_attrs = entities.Organization().create_json()
        cls.hostgroup_name = entities.HostGroup().create_json()['name']
        cls.org_name = org_attrs['name']
        cls.org_id = org_attrs['id']
        cls.org_label = org_attrs['label']

        super(DiscoveryRules, cls).setUpClass()

    @data(*generate_strings_list(len1=8))
    def test_positive_create_discovery_rule_1(self, name):
        """@Test: Create Discovery Rule

        @Feature: Foreman Discovery

        @Assert: Rule should be successfully created

        """
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.hostgroup_name)
            self.assertIsNotNone(self.discoveryrules.search(name))

    def test_positive_create_discovery_rule_2(self):
        """@Test: Create Discovery Rule with 255 characters in name

        @Feature: Foreman Discovery

        @Assert: Rule should be successfully created

        """
        name = gen_string('alpha', 255)
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.hostgroup_name)
            self.assertIsNotNone(self.discoveryrules.search(name))

    def test_negative_create_discovery_rule_1(self):
        """@Test: Create Discovery Rule with 256 characters in name

        @Feature: Foreman Discovery

        @Assert: Error should be raised and rule should not be created

        """
        name = gen_string('alpha', 256)
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.hostgroup_name)
            self.assertIsNotNone(self.discoveryrules.wait_until_element(
                common_locators['name_haserror']
            ))
            self.assertIsNone(self.discoveryrules.search(name))

    @data("", "  ")
    def test_negative_create_discovery_rule_2(self, name):
        """@Test: Create Discovery Rule with blank and whitespace in name

        @Feature: Foreman Discovery

        @Assert: Error should be raised and rule should not be created

        """
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.hostgroup_name)
            self.assertIsNotNone(self.discoveryrules.wait_until_element(
                common_locators['name_haserror']
            ))
            self.assertIsNone(self.discoveryrules.search(name))

    @data('-1', gen_string("alpha", 6))
    def test_negative_create_discovery_rule_3(self, limit):
        """@Test: Create Discovery Rule with invalid host limit

        @Feature: Foreman Discovery

        @Assert: Error should be raised and rule should not be created

        """
        name = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.hostgroup_name, host_limit=limit)
            self.assertIsNotNone(self.discoveryrules.wait_until_element(
                common_locators['haserror']
            ))
            self.assertIsNone(self.discoveryrules.search(name))

    def test_negative_create_discovery_rule_4(self):
        """@Test: Create Discovery Rule with name that already exists

        @Feature: Foreman Discovery

        @Assert: Error should be raised and rule should not be created

        """
        name = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.hostgroup_name)
            self.assertIsNotNone(self.discoveryrules.search(name))
            make_discoveryrule(session, name=name,
                               hostgroup=self.hostgroup_name)
            self.assertIsNotNone(self.discoveryrules.wait_until_element(
                common_locators['name_haserror']
            ))

    def test_negative_create_discovery_rule_5(self):
        """@Test: Create Discovery Rule with invalid priority

        @Feature: Foreman Discovery

        @Assert: Error should be raised and rule should not be created

        """
        name = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.hostgroup_name,
                               priority=gen_string('alpha', 6))
            self.assertIsNotNone(self.discoveryrules.wait_until_element(
                common_locators['haserror']
            ))
            self.assertIsNone(self.discoveryrules.search(name))

    def test_disable_discovery_rule_1(self):
        """@Test: Disable Discovery Rule while creation

        @Feature: Foreman Discovery

        @Assert: Rule should be disabled

        """
        name = gen_string("alpha", 6)
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.hostgroup_name, enable=True)
            self.assertIsNotNone(self.discoveryrules.search(name))

    @data(*generate_strings_list(len1=8))
    def test_delete_discovery_rule_1(self, name):
        """@Test: Delete Discovery Rule

        @Feature: Foreman Discovery

        @Assert: Rule should be successfully created

        """
        with Session(self.browser) as session:
            make_discoveryrule(session, name=name,
                               hostgroup=self.hostgroup_name)
            self.assertIsNotNone(self.discoveryrules.search(name))
            self.discoveryrules.delete(name)
            self.assertIsNone(self.discoveryrules.search(name))
