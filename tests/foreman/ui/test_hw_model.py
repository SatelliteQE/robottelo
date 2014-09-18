"""Test class for Config Groups UI"""

from ddt import ddt
from fauxfactory import FauxFactory
from nose.plugins.attrib import attr
from robottelo.common.decorators import data
from robottelo.common.helpers import generate_strings_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_org, make_loc, make_hw_model
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@ddt
class HardwareModelTestCase(UITestCase):
    """Implements Hardware Model tests in UI."""
    org_name = None
    loc_name = None

    def setUp(self):
        super(HardwareModelTestCase, self).setUp()
        # Make sure to use the Class' org_name instance
        if (HardwareModelTestCase.org_name is None and
                HardwareModelTestCase.loc_name is None):
            HardwareModelTestCase.org_name = FauxFactory.generate_string(
                "alpha", 8)
            HardwareModelTestCase.loc_name = FauxFactory.generate_string(
                "alpha", 8)
            with Session(self.browser) as session:
                make_org(session, org_name=HardwareModelTestCase.org_name)
                make_loc(session, name=HardwareModelTestCase.loc_name)

    @attr('ui', 'hardware-model', 'implemented')
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

    @attr('ui', 'hardware-model', 'implemented')
    @data(
        FauxFactory.generate_string('alphanumeric', 255),
        FauxFactory.generate_string('alpha', 255),
        FauxFactory.generate_string('numeric', 255),
        FauxFactory.generate_string('latin1', 255),
        FauxFactory.generate_string('utf8', 255)
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

    @attr('ui', 'hardware-model', 'implemented')
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

    @attr('ui', 'hardware-model', 'implemented')
    @data({'name': FauxFactory.generate_string('alpha', 10),
           'new_name': FauxFactory.generate_string('alpha', 10)},
          {'name': FauxFactory.generate_string('numeric', 10),
           'new_name': FauxFactory.generate_string('numeric', 10)},
          {'name': FauxFactory.generate_string('alphanumeric', 10),
           'new_name': FauxFactory.generate_string('alphanumeric', 10)},
          {'name': FauxFactory.generate_string('utf8', 10),
           'new_name': FauxFactory.generate_string('utf8', 10)},
          {'name': FauxFactory.generate_string('latin1', 20),
           'new_name': FauxFactory.generate_string('latin1', 10)})
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

    @attr('ui', 'hardware-model', 'implemented')
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
            self.assertIsNotNone(session.nav.wait_until_element
                                 (common_locators["notif.success"]))
            self.assertIsNone(self.hardwaremodel.search(name))
