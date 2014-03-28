# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Life cycle environments UI
"""

from nose.plugins.attrib import attr
from robottelo.common.helpers import generate_name
from robottelo.ui.factory import make_org
from robottelo.ui.locators import common_locators
from tests.ui.baseui import BaseUI


class ContentEnvironment(BaseUI):
    """
    Implements Life cycle content environment tests in UI
    """

    org_name = None

    def setUp(self):
        super(ContentEnvironment, self).setUp()
        # Make sure to use the Class' org_name instance
        if ContentEnvironment.org_name is None:
            ContentEnvironment.org_name = generate_name(8, 8)
            make_org(ContentEnvironment.org_name)

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_create_content_environment_1(self):
        """
        @Feature: Content Environment - Positive Create
        @Test: Create Content Environment with minimal input parameters
        @Assert: Environment is created
        """
        name = generate_name(6)
        description = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(name, description)
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_create_content_environment_2(self):
        """
        @Feature: Content Environment - Positive Create
        @Test: Create Content Environment in a chain
        @Assert: Environment is created
        """
        env_name1 = generate_name(6)
        env_name2 = generate_name(6)
        description = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(env_name1, description)
        self.contentenv.create(env_name2, description, prior=env_name1)
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_delete_content_environment_1(self):
        """
        @Feature: Content Environment - Positive Delete
        @Test: Create Content Environment and delete it
        @Assert: Environment is deleted
        """
        name = generate_name(6)
        description = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(name, description)
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))
        self.contentenv.delete(name, "true")
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_update_content_environment_1(self):
        """
        @Feature: Content Environment - Positive Update
        @Test: Create Content Environment and update it
        @Assert: Environment is updated
        """
        name = generate_name(6)
        new_name = generate_name(6)
        description = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_select_org(self.org_name)
        self.navigator.go_to_life_cycle_environments()
        self.contentenv.create(name)
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))
        self.contentenv.update(name, new_name, description)
        self.assertTrue(self.contentenv.wait_until_element
                        (common_locators["alert.success"]))
