"""Test class for Config Groups UI

:Requirement: Hw Model

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from robottelo.datafactory import (
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.factory import make_hw_model
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class HardwareModelTestCase(UITestCase):
    """Implements Hardware Model tests in UI."""

    @tier1
    def test_positive_create_with_name(self):
        """Create new Hardware-Model

        :id: e2ebac95-4d0b-404d-98c6-dcba40158c28

        :expectedresults: Hardware-Model is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_hw_model(session, name=name)
                    self.assertIsNotNone(self.hardwaremodel.search(name))

    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create new Hardware-Model with invalid names

        :id: ccaeec78-28e9-432d-bb2e-6fb92280d996

        :expectedresults: Hardware-Model is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_hw_model(session, name=name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @tier1
    def test_positive_update(self):
        """Updates the Hardware-Model

        :id: 56ec6d62-1520-4de2-9231-b62e57578223

        :expectedresults: Hardware-Model is updated.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_hw_model(session, name=name)
            self.assertIsNotNone(self.hardwaremodel.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.hardwaremodel.update(name, new_name)
                    self.assertIsNotNone(self.hardwaremodel.search(new_name))
                    name = new_name  # for next iteration

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Deletes the Hardware-Model

        :id: 160319bb-c67c-4086-8d48-fce88c110a2e

        :expectedresults: Hardware-Model is deleted

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_hw_model(session, name=name)
                    self.hardwaremodel.delete(name)
