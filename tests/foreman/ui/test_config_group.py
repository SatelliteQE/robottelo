"""Test class for Config Groups UI

:Requirement: Config Group

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from robottelo.datafactory import (
    generate_strings_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import run_only_on, tier1, upgrade
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

        :id: b9e170a3-29b1-49e6-bfc6-c48fb0021ecb

        :expectedresults: Config-Groups is created


        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_config_groups(session, name=name)
                    self.assertIsNotNone(self.configgroups.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create(self):
        """Try to create config group and use whitespace, blank, tab
        symbol or too long string of different types as its name value

        :id: 1c8d098c-60c2-4dc4-af24-1c8a4cfff5e2

        :expectedresults: Config-Groups is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
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

        :id: c8589969-1fdb-4977-b973-3795a36704be

        :expectedresults: Config-Groups is updated.


        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_config_groups(session, name=name)
            self.assertIsNotNone(self.configgroups.search(name))
            for new_name in generate_strings_list():
                with self.subTest(new_name):
                    self.configgroups.update(name, new_name)
                    self.assertIsNotNone(self.configgroups.search(new_name))
                    name = new_name

    @run_only_on('sat')
    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete selected config-groups

        :id: 50879d3c-7c38-4294-aae4-0f3f146c9613

        :expectedresults: Config-Groups is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_config_groups(session, name=name)
                    self.configgroups.delete(name)
