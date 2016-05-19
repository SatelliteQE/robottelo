import unittest2

from fauxfactory import gen_string
from nailgun import entities
from robottelo.config import settings
from robottelo.constants import OSCAP_DEFAULT_CONTENT
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import skip_if_bug_open, tier1, tier2
from robottelo.helpers import get_data_file
from robottelo.test import UITestCase
from robottelo.ui.factory import make_oscapcontent
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class OpenScapContentTestCase(UITestCase):
    """Implements Oscap Content tests in UI."""

    @classmethod
    def setUpClass(cls):
        super(OpenScapContentTestCase, cls).setUpClass()
        path = settings.oscap.content_path
        cls.content_path = get_data_file(path)

    @tier1
    def test_positive_create(self):
        """Create OpenScap content.

        @Feature: OpenScap - Positive Create.

        @Steps:

        1. Create an openscap content.
        2. Provide all the appropriate parameters.

        @Assert: Whether creating  content for OpenScap is successful.
        """
        with Session(self.browser) as session:
            for content_name in valid_data_list():
                with self.subTest(content_name):
                    make_oscapcontent(
                        session,
                        name=content_name,
                        content_path=self.content_path,
                    )
                    self.assertIsNotNone(
                        self.oscapcontent.search(content_name))

    @skip_if_bug_open('bugzilla', 1289571)
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create OpenScap content with negative values

        @Feature: OpenScap - Negative Create.

        @Steps:

        1. Create an openscap content.
        2. Provide all the appropriate parameters.

        @Assert: Creating content for OpenScap is not successful.

        @BZ: 1289571
        """
        with Session(self.browser) as session:
            for content_name in invalid_values_list(interface='ui'):
                with self.subTest(content_name):
                    make_oscapcontent(
                        session,
                        name=content_name,
                        content_path=self.content_path,
                    )
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['haserror']))

    @tier1
    @unittest2.skip('oscap contents are not installed by default.'
                    'Installer needs to be fixed')
    def test_positive_default(self):
        """Check whether OpenScap content exists by default.

        @Feature: OpenScap - Test Default Content.

        @Steps:

        1. Set Org as Any Org.
        2. Navigate to oscap Content page.

        @Assert: Whether oscap content exists by default.
        """
        # see BZ 1336374
        with Session(self.browser):
            self.assertIsNotNone(self.oscapcontent.search(
                OSCAP_DEFAULT_CONTENT['rhel7_content']))
            self.assertIsNotNone(self.oscapcontent.search(
                OSCAP_DEFAULT_CONTENT['rhel6_content']))

    @tier2
    def test_positive_update(self):
        """Update OpenScap content.

        @Feature: OpenScap - Positive Update.

        @Steps:

        1. Create an openscap content.
        2. Provide all the appropriate parameters.
        3. Update the openscap content, here the Org.

        @Assert: Whether creating  content for OpenScap is successful.
        """
        org = entities.Organization(name=gen_string('alpha')).create()
        content_name = gen_string('alpha')
        with Session(self.browser) as session:
            make_oscapcontent(
                session,
                name=content_name,
                content_path=self.content_path,
            )
            self.oscapcontent.update(content_name, content_org=org.name)
            session.nav.go_to_select_org(org.name)
            self.assertIsNotNone(
                self.oscapcontent.search(content_name))

    @tier1
    def test_positive_delete(self):
        """Create OpenScap content and then delete it.

        @Feature: OpenScap - Delete.

        @Steps:

        1. Create an openscap content.
        2. Provide all the appropriate parameters.
        3. Delete the openscap content.

        @Assert: Deleting content for OpenScap is successful.
        """
        with Session(self.browser) as session:
            for content_name in valid_data_list():
                with self.subTest(content_name):
                    make_oscapcontent(
                        session,
                        name=content_name,
                        content_path=self.content_path,
                    )
                    self.assertIsNotNone(
                        self.oscapcontent.search(content_name))
                    self.oscapcontent.delete(content_name)
