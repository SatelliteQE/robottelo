"""Test class for Compute Profile UI

:Requirement: Computeprofile

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from fauxfactory import gen_string
from robottelo.datafactory import invalid_values_list, valid_data_list
from robottelo.decorators import tier1, upgrade
from robottelo.test import UITestCase
from robottelo.ui.factory import make_compute_profile
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class ComputeProfileTestCase(UITestCase):
    """Implements Compute Profile tests in UI."""

    @tier1
    def test_positive_create(self):
        """Create new Compute Profile using different names

        :id: 138a3e6f-7eb5-4204-b48d-edc6ce363576

        :expectedresults: Compute Profile is created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_compute_profile(session, name=name)
                    self.assertIsNotNone(self.compute_profile.search(name))

    @tier1
    def test_negative_create(self):
        """Attempt to create Compute Profile using invalid names only

        :id: 6da73996-c235-45ee-a11e-5b4f0ae75d93

        :expectedresults: Compute Profile is not created

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in invalid_values_list('ui'):
                with self.subTest(name):
                    make_compute_profile(session, name=name)
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['name_haserror']))

    @tier1
    def test_positive_update(self):
        """Update selected Compute Profile entity using proper names

        :id: b6dac9a4-8c5d-44d4-91e4-be2813e3ea50

        :expectedresults: Compute Profile is updated.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_compute_profile(session, name=name)
            self.assertIsNotNone(self.compute_profile.search(name))
            for new_name in valid_data_list():
                with self.subTest(new_name):
                    self.compute_profile.update(name, new_name)
                    self.assertIsNotNone(self.compute_profile.search(new_name))
                    name = new_name

    @tier1
    def test_negative_update(self):
        """Attempt to update Compute Profile entity using invalid names only

        :id: cf7d46c2-6edc-43be-b5d4-ba92f10b921b

        :expectedresults: Compute Profile is not updated.

        :CaseImportance: Critical
        """
        name = gen_string('alpha')
        with Session(self) as session:
            make_compute_profile(session, name=name)
            self.assertIsNotNone(self.compute_profile.search(name))
            for new_name in invalid_values_list('ui'):
                with self.subTest(new_name):
                    self.compute_profile.update(name, new_name)
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['name_haserror']))

    @tier1
    @upgrade
    def test_positive_delete(self):
        """Delete Compute Profile entity

        :id: 9029b8ec-44c3-4f41-9ea0-0c13c2add76c

        :expectedresults: Compute Profile is deleted successfully.

        :CaseImportance: Critical
        """
        with Session(self) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_compute_profile(session, name=name)
                    self.compute_profile.delete(name, dropdown_present=True)
