"""Test class for Config Groups UI"""

from fauxfactory import gen_string
from robottelo.datafactory import (
    generate_strings_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import run_only_on, tier1
from robottelo.test import UITestCase
from robottelo.ui.factory import make_config_groups
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class ConfigGroupTestCase(UITestCase):
    """Implements Config Groups tests in UI."""

    @run_only_on('sat')
    @tier1
    def test_positive_create(self):
        """Create new Config-Group

        @Feature: Config-Groups - Positive Create

        @Assert: Config-Groups is created

        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_config_groups(session, name=name)
                    self.assertIsNotNone(self.configgroups.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create(self):
        """Try to create config group and use whitespace, blank, tab
        symbol or too long string of different types as its name value

        @Feature: Config-Groups - Negative Create

        @Assert: Config-Groups is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list('ui'):
                with self.subTest(name):
                    make_config_groups(session, name=name)
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['name_haserror']))
                    self.assertIsNone(self.configgroups.search(name))

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """Update selected config-group

        @Feature: Config-Groups - Positive Update

        @Assert: Config-Groups is updated.

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    make_config_groups(session, name=name)
                    self.assertIsNotNone(self.configgroups.search(name))
                    self.configgroups.update(name, new_name)
                    self.assertIsNotNone(self.configgroups.search(new_name))

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Delete selected config-groups

        @Feature: Config-Groups - Positive delete

        @Assert: Config-Groups is deleted

        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=8):
                with self.subTest(name):
                    make_config_groups(session, name=name)
                    self.configgroups.delete(name)
