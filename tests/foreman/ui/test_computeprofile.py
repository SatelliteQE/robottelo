"""Test class for Compute Profile UI"""

from fauxfactory import gen_string
from robottelo.datafactory import (
    generate_strings_list,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import tier1
from robottelo.test import UITestCase
from robottelo.ui.factory import make_compute_profile
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


class ComputeProfileTestCase(UITestCase):
    """Implements Compute Profile tests in UI."""

    @tier1
    def test_positive_create(self):
        """Create new Compute Profile using different names

        @Feature: Compute Profile - Positive Create

        @Assert: Compute Profile is created
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_compute_profile(session, name=name)
                    self.assertIsNotNone(self.compute_profile.search(name))

    @tier1
    def test_negative_create(self):
        """Attempt to create Compute Profile using invalid names only

        @Feature: Compute Profile - Negative Create

        @Assert: Compute Profile is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list('ui'):
                with self.subTest(name):
                    make_compute_profile(session, name=name)
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['name_haserror']))

    @tier1
    def test_positive_update(self):
        """Update selected Compute Profile entity using proper names

        @Feature: Compute Profile - Positive Update

        @Assert: Compute Profile is updated.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_compute_profile(session, name=name)
            self.assertIsNotNone(self.compute_profile.search(name))
            for new_name in generate_strings_list(length=7):
                with self.subTest(new_name):
                    self.compute_profile.update(name, new_name)
                    self.assertIsNotNone(self.compute_profile.search(new_name))
                    name = new_name

    @tier1
    def test_negative_update(self):
        """Attempt to update Compute Profile entity using invalid names only

        @Feature: Compute Profile - Negative Update

        @Assert: Compute Profile is not updated.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_compute_profile(session, name=name)
            self.assertIsNotNone(self.compute_profile.search(name))
            for new_name in invalid_values_list('ui'):
                with self.subTest(new_name):
                    self.compute_profile.update(name, new_name)
                    self.assertIsNotNone(session.nav.wait_until_element(
                        common_locators['name_haserror']))

    @tier1
    def test_positive_delete(self):
        """Delete Compute Profile entity

        @Feature: Compute Profile - Positive Delete

        @Assert: Compute Profile is deleted successfully.
        """
        with Session(self.browser) as session:
            for name in generate_strings_list(length=7):
                with self.subTest(name):
                    make_compute_profile(session, name=name)
                    self.compute_profile.delete(name)
