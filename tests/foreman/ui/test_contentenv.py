# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai
"""Test class for Life cycle environments UI"""

from fauxfactory import FauxFactory
from nose.plugins.attrib import attr
from robottelo.test import UITestCase
from robottelo.ui.factory import make_org, make_lifecycle_environment
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class ContentEnvironment(UITestCase):
    """Implements Life cycle content environment tests in UI"""

    org_name = None

    def setUp(self):
        super(ContentEnvironment, self).setUp()
        # Make sure to use the Class' org_name instance
        if ContentEnvironment.org_name is None:
            ContentEnvironment.org_name = FauxFactory.generate_string(
                "alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=ContentEnvironment.org_name)

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_create_content_environment_1(self):
        """@Test: Create content environment with minimal input parameters

        @Feature: Content Environment - Positive Create

        @Assert: Environment is created

        """

        name = FauxFactory.generate_string("alpha", 6)
        description = FauxFactory.generate_string("alpha", 6)
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=name, description=description)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_create_content_environment_2(self):
        """@Test: Create Content Environment in a chain

        @Feature: Content Environment - Positive Create

        @Assert: Environment is created

        """

        env_1_name = FauxFactory.generate_string("alpha", 6)
        env_2_name = FauxFactory.generate_string("alpha", 6)
        description = FauxFactory.generate_string("alpha", 6)
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=env_1_name,
                                       description=description)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))
            self.contentenv.create(env_2_name, description, prior=env_1_name)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_delete_content_environment_1(self):
        """@Test: Create Content Environment and delete it

        @Feature: Content Environment - Positive Delete

        @Assert: Environment is deleted

        """

        name = FauxFactory.generate_string("alpha", 6)
        description = FauxFactory.generate_string("alpha", 6)
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=name, description=description)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))
            self.contentenv.delete(name, "true")
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))

    @attr('ui', 'contentenv', 'implemented')
    def test_positive_update_content_environment_1(self):
        """@Test: Create Content Environment and update it

        @Feature: Content Environment - Positive Update

        @Assert: Environment is updated

        """

        name = FauxFactory.generate_string("alpha", 6)
        new_name = FauxFactory.generate_string("alpha", 6)
        description = FauxFactory.generate_string("alpha", 6)
        with Session(self.browser) as session:
            make_lifecycle_environment(session, org=self.org_name,
                                       name=name)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))
            self.contentenv.update(name, new_name, description)
            self.assertIsNotNone(self.contentenv.wait_until_element
                                 (common_locators["alert.success"]))
