"""Test class for Config Groups UI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.common.decorators import data, run_only_on
from robottelo.common.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_config_groups
from robottelo.ui.locators import common_locators, locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class ConfigGroups(UITestCase):
    """Implements Config Groups tests in UI."""

    @data(*generate_strings_list(len1=8))
    def test_create_positive_1(self, name):
        """@Test: Create new Config-Group

        @Feature: Config-Groups - Positive Create

        @Assert: Config-Groups is created

        """
        with Session(self.browser) as session:
            make_config_groups(session, name=name)
            search = self.configgroups.search(name)
            self.assertIsNotNone(search)

    @data(
        gen_string('alphanumeric', 255),
        gen_string('alpha', 255),
        gen_string('numeric', 255),
        gen_string('latin1', 255),
        gen_string('utf8', 255)
    )
    def test_create_positive_2(self, name):
        """@Test: Create new config-groups with 255 chars

        @Feature: Config-Groups - Positive Create

        @Assert: Config-Groups is created with 255 chars

        """
        with Session(self.browser) as session:
            make_config_groups(session, name=name)
            search = self.configgroups.search(name)
            self.assertIsNotNone(search)

    @data(*generate_strings_list(len1=256))
    def test_create_negative_1(self, name):
        """@Test: Create new config-groups with 256 chars

        @Feature: Config-Groups - Negative Create

        @Assert: Config-Groups is not created

        """
        with Session(self.browser) as session:
            make_config_groups(session, name=name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)
            search = self.configgroups.search(name)
            self.assertIsNone(search)

    @data("", "  ")
    def test_create_negative_2(self, name):
        """@Test: Create new config-groups with blank name

        @Feature: Config-Groups - Negative Create

        @Assert: Config-Groups is not created

        """

        with Session(self.browser) as session:
            make_config_groups(session, name=name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    @data({'name': gen_string('alpha', 10),
           'new_name': gen_string('alpha', 10)},
          {'name': gen_string('numeric', 10),
           'new_name': gen_string('numeric', 10)},
          {'name': gen_string('alphanumeric', 10),
           'new_name': gen_string('alphanumeric', 10)},
          {'name': gen_string('utf8', 10),
           'new_name': gen_string('utf8', 10)},
          {'name': gen_string('latin1', 20),
           'new_name': gen_string('latin1', 10)})
    def test_update_positive_1(self, testdata):
        """@Test: Create new config-group

        @Feature: Config-Groups - Positive Update

        @Assert: Config-Groups is updated.

        """
        name = testdata['name']
        new_name = testdata['new_name']
        with Session(self.browser) as session:
            make_config_groups(session, name=name)
            search = self.configgroups.search(name)
            self.assertIsNotNone(search)
            self.configgroups.update(name, new_name)
            search = self.configgroups.search(new_name)
            self.assertIsNotNone(search)

    @data(*generate_strings_list(len1=8))
    def test_delete_positive_1(self, name):
        """@Test: Create new config-groups

        @Feature: Config-Groups - Positive delete

        @Assert: Config-Groups is deleted

        """

        with Session(self.browser) as session:
            make_config_groups(session, name=name)
            search = self.configgroups.search(name)
            self.assertIsNotNone(search)
            self.configgroups.delete(
                name, True, drop_locator=locators["config_groups.dropdown"])
            self.assertIsNotNone(session.nav.wait_until_element
                                 (common_locators["notif.success"]))
            self.assertIsNone(self.configgroups.search(name))
