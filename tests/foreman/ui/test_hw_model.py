"""Test class for Config Groups UI"""

from ddt import ddt
from fauxfactory import gen_string
from robottelo.decorators import bz_bug_is_open, data, run_only_on
from robottelo.helpers import generate_strings_list, valid_data_list
from robottelo.test import UITestCase
from robottelo.ui.factory import make_hw_model
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@run_only_on('sat')
@ddt
class HardwareModelTestCase(UITestCase):
    """Implements Hardware Model tests in UI."""

    @data(*valid_data_list())
    def test_create_positive_different_names(self, name):
        """@test: Create new Hardware-Model

        @feature: Hardware-Model - Positive Create

        @assert: Hardware-Model is created

        """
        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            search = self.hardwaremodel.search(name)
            self.assertIsNotNone(search)

    @data(*generate_strings_list(len1=256))
    def test_create_negative_with_too_long_names(self, name):
        """@test: Create new Hardware-Model with 256 chars

        @feature: Hardware-Model - Negative Create

        @assert: Hardware-Model is not created

        """
        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @data('', '   ')
    def test_create_negative_with_blank_name(self, name):
        """@test: Create new Hardware-Model with blank name

        @feature: Hardware-Model - Negative Create

        @assert: Hardware-Model is not created

        """
        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            error = session.nav.wait_until_element(
                common_locators['name_haserror'])
            self.assertIsNotNone(error)

    @data(*valid_data_list())
    def test_update_positive(self, new_name):
        """@test: Updates the Hardware-Model

        @feature: Hardware-Model - Positive Update

        @assert: Hardware-Model is updated.

        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            search = self.hardwaremodel.search(name)
            self.assertIsNotNone(search)
            self.hardwaremodel.update(name, new_name)
            search = self.hardwaremodel.search(new_name)
            self.assertIsNotNone(search)

    @data(
        {u'name': gen_string('alpha')},
        {u'name': gen_string('numeric')},
        {u'name': gen_string('alphanumeric')},
        {u'name': gen_string('html'), 'bugzilla': 1265150},
        {u'name': gen_string('latin1')},
        {u'name': gen_string('utf8')})
    def test_delete_positive(self, test_data):
        """@test: Deletes the Hardware-Model

        @feature: Hardware-Model - Positive delete

        @assert: Hardware-Model is deleted

        """
        with Session(self.browser) as session:
            bug_id = test_data.pop('bugzilla', None)
            if bug_id is not None and bz_bug_is_open(bug_id):
                self.skipTest(
                    'Bugzilla bug {0} is open for html data.'.format(bug_id)
                )

            name = test_data['name']
            make_hw_model(session, name=name)
            self.hardwaremodel.delete(name)
