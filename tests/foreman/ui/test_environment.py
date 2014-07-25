# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Environment UI
"""

from ddt import ddt
from nose.plugins.attrib import attr
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_string, generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_org, make_loc, make_env
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class Environment(UITestCase):
    """
    Implements environment tests in UI
    """
    org_name = None
    loc_name = None

    def setUp(self):
        super(Environment, self).setUp()
        # Make sure to use the Class' org_name instance
        if (Environment.org_name is None and
           Environment.loc_name is None):
            Environment.org_name = generate_string("alpha", 8)
            Environment.loc_name = generate_string("alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=Environment.org_name)
                make_loc(session, name=Environment.loc_name)

    @attr('ui', 'environment', 'implemented')
    @data({'name': generate_string('alpha', 8)},
          {'name': generate_string('numeric', 8)},
          {'name': generate_string('alphanumeric', 8)})
    def test_create_env_positive_1(self, name):
        """
        @Test: Create new environment
        @Feature: Environment - Positive Create
        @Assert: Environment is created
        """
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_env(session, name=name, orgs=[org_name])
            search = self.environment.search(name)
            self.assertIsNotNone(search)

    @attr('ui', 'environment', 'implemented')
    @data({'name': generate_string('alpha', 255)},
          {'name': generate_string('numeric', 255)},
          {'name': generate_string('alphanumeric', 255)})
    def test_create_env_positive_2(self, testdata):
        """
        @Test: Create new environment with 255 chars
        @Feature: Environment - Positive Create
        @Assert: Environment is created
        """
        name = testdata['name']
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_env(session, name=name, orgs=[org_name])
            search = self.environment.search(name)
            self.assertIsNotNone(search)

    @attr('ui', 'environment', 'implemented')
    @data(*generate_strings_list(len1=256))
    def test_create_env_negative_1(self, name):
        """
        @Test: Create new environment with 256 chars
        @Feature: Environment - Negative Create
        @Assert: Environment is not created
        """
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_env(session, name=name, orgs=[org_name])
            search = self.environment.search(name)
            self.assertIsNone(search)

    def test_create_env_negative_2(self):
        """
        @Test: Create new environment with blank name
        @Feature: Environment - Negative Create
        @Assert: Environment is not created
        """
        name = ""
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_env(session, name=name, orgs=[org_name])
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    def test_create_env_negative_3(self):
        """
        @Test: Create new environment with whitespace name
        @Feature: Environment - Negative Create
        @Assert: Environment is not created
        """
        name = "   "
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_env(session, name=name, orgs=[org_name])
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    @attr('ui', 'environment', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_update_env(self, new_name):
        """
        @Test: Update an environment and associated OS
        @Feature: Environment - Positive Update
        @Assert: Environment is updated
        """
        name = generate_string("alpha", 6)
        org_name = generate_string("alpha", 8)
        new_org = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_env(session, name=name, orgs=[org_name])
            self.environment.update(name, [org_name], [new_org],
                                    new_name=new_name)
            search = self.environment.search(new_name)
            self.assertIsNotNone(search)

    @attr('ui', 'environment', 'implemented')
    @data(*generate_strings_list(len1=8))
    def test_remove_env(self, name):
        """
        @Test: Delete an environment
        @Feature: Environment - Positive Delete
        @Assert: Environment is deleted
        """
        org_name = generate_string("alpha", 8)
        with Session(self.browser) as session:
            make_env(session, name=name, orgs=[org_name])
            self.environment.delete(name, really=True)
            notif = session.nav.wait_until_element(
                common_locators["notif.success"])
            self.assertTrue(notif)
