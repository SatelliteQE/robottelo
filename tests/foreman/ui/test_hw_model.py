"""Test class for Config Groups UI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.common.decorators import data, run_only_on
from robottelo.common.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_hw_model
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class HardwareModelTestCase(UITestCase):
    """Implements Hardware Model tests in UI."""

    @data(*generate_strings_list(len1=8))
    def test_create_positive_1(self, name):
        """@test: Create new Hardware-Model

        @feature: Hardware-Model - Positive Create

        @assert: Hardware-Model is created

        """
        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            search = self.hardwaremodel.search(name)
            self.assertIsNotNone(search)

    @data(
        gen_string('alphanumeric', 255),
        gen_string('alpha', 255),
        gen_string('numeric', 255),
        gen_string('latin1', 255),
        gen_string('utf8', 255)
    )
    def test_create_positive_2(self, name):
        """@test: Create new Hardware-Model with 255 chars

        @feature: Hardware-Model - Positive Create

        @assert: Hardware-Model is created with 255 chars

        """
        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            search = self.hardwaremodel.search(name)
            self.assertIsNotNone(search)

    @data(*generate_strings_list(len1=256))
    def test_create_negative_1(self, name):
        """@test: Create new Hardware-Model with 256 chars

        @feature: Hardware-Model - Negative Create

        @assert: Hardware-Model is not created

        """
        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    def test_create_negative_2(self):
        """@test: Create new Hardware-Model with blank name

        @feature: Hardware-Model - Negative Create

        @assert: Hardware-Model is not created

        """
        name = ""
        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    def test_create_negative_3(self):
        """@test: Create new Hardware-Model with whitespace name

        @feature: Hardware-Model - Negative Create

        @assert: Hardware-Model is not created

        """
        name = "    "
        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            error = session.nav.wait_until_element(
                common_locators["name_haserror"])
            self.assertIsNotNone(error)

    @data({'name': gen_string('alpha'),
           'new_name': gen_string('alpha')},
          {'name': gen_string('numeric'),
           'new_name': gen_string('numeric')},
          {'name': gen_string('alphanumeric'),
           'new_name': gen_string('alphanumeric')},
          {'name': gen_string('utf8'),
           'new_name': gen_string('utf8')},
          {'name': gen_string('latin1'),
           'new_name': gen_string('latin1')})
    def test_update_positive_1(self, testdata):
        """@test: Updates the Hardware-Model

        @feature: Hardware-Model - Positive Update

        @assert: Hardware-Model is updated.

        """
        name = testdata['name']
        new_name = testdata['new_name']
        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            search = self.hardwaremodel.search(name)
            self.assertIsNotNone(search)
            self.hardwaremodel.update(name, new_name)
            search = self.hardwaremodel.search(new_name)
            self.assertIsNotNone(search)

    @data(*generate_strings_list(len1=8))
    def test_delete_positive_1(self, name):
        """@test: Deletes the Hardware-Model

        @feature: Hardware-Model - Positive delete

        @assert: Hardware-Model is deleted

        """

        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            search = self.hardwaremodel.search(name)
            self.assertIsNotNone(search)
            self.hardwaremodel.delete(name, True)
            self.assertIsNone(self.hardwaremodel.search(name, timeout=3))
