# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Test class for Life cycle environments UI
"""

from nose.plugins.attrib import attr
from robottelo.common.helpers import generate_name
from robottelo.ui.locators import common_locators
from tests.ui.baseui import BaseUI


class ContentEnvironment(BaseUI):
    """
    Implements Life cycle content environment tests in UI
    """

    @attr('ui', 'content_env', 'implemented')
    def test_positive_create_content_environment_1(self):
        """
        @Feature: Content Environment - Positive Create
        @Test: Create Content Environment with minimal input parameters
        @Assert: Environment is created
        """
        name = generate_name(6)
        description = generate_name(6)
        org_name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.navigator.go_to_select_org(org_name)
        self.navigator.go_to_life_cycle_environments()
        self.content_environment.create(name, description)
        self.assertTrue(self.content_environment.wait_until_element
                        (common_locators["alert.success"]))

    @attr('ui', 'content_env', 'implemented')
    def test_positive_delete_content_environment_1(self):
        """
        @Feature: Content Environment - Delete Create
        @Test: Create Content Environment with minimal input parameters
        @Assert: Environment is deleted
        """
        name = generate_name(6)
        description = generate_name(6)
        org_name = generate_name(6)
        self.login.login(self.katello_user, self.katello_passwd)
        self.navigator.go_to_org()
        self.org.create(org_name)
        self.navigator.go_to_org()
        self.navigator.go_to_select_org(org_name)
        self.navigator.go_to_life_cycle_environments()
        self.content_environment.create(name, description)
        self.assertTrue(self.content_environment.wait_until_element
                        (common_locators["alert.success"]))
        self.content_environment.delete(name, "true")
