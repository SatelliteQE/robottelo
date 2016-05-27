"""Test class for Config Groups UI"""

from fauxfactory import gen_string
from robottelo.datafactory import (
    datacheck,
    invalid_values_list,
    valid_data_list,
)
from robottelo.decorators import bz_bug_is_open, run_only_on, tier1
from robottelo.test import UITestCase
from robottelo.ui.factory import make_hw_model
from robottelo.ui.locators import common_locators
from robottelo.ui.session import Session


@datacheck
def valid_hw_model_names():
    """Returns a list of valid hw model names"""
    return [
        {u'name': gen_string('alpha')},
        {u'name': gen_string('numeric')},
        {u'name': gen_string('alphanumeric')},
        {u'name': gen_string('html'), 'bugzilla': 1265150},
        {u'name': gen_string('latin1')},
        {u'name': gen_string('utf8')}
    ]


class HardwareModelTestCase(UITestCase):
    """Implements Hardware Model tests in UI."""

    @run_only_on('sat')
    @tier1
    def test_positive_create_with_name(self):
        """Create new Hardware-Model

        @feature: Hardware-Model - Positive Create

        @assert: Hardware-Model is created
        """
        with Session(self.browser) as session:
            for name in valid_data_list():
                with self.subTest(name):
                    make_hw_model(session, name=name)
                    self.assertIsNotNone(self.hardwaremodel.search(name))

    @run_only_on('sat')
    @tier1
    def test_negative_create_with_invalid_name(self):
        """Create new Hardware-Model with invalid names

        @feature: Hardware-Model - Negative Create

        @assert: Hardware-Model is not created
        """
        with Session(self.browser) as session:
            for name in invalid_values_list(interface='ui'):
                with self.subTest(name):
                    make_hw_model(session, name=name)
                    error = session.nav.wait_until_element(
                        common_locators['name_haserror'])
                    self.assertIsNotNone(error)

    @run_only_on('sat')
    @tier1
    def test_positive_update(self):
        """Updates the Hardware-Model

        @feature: Hardware-Model - Positive Update

        @assert: Hardware-Model is updated.
        """
        name = gen_string('alpha')
        with Session(self.browser) as session:
            make_hw_model(session, name=name)
            self.assertIsNotNone(self.hardwaremodel.search(name))
            for test_data in valid_hw_model_names():
                with self.subTest(test_data):
                    bug_id = test_data.pop('bugzilla', None)
                    if bug_id is not None and bz_bug_is_open(bug_id):
                        self.skipTest(
                            'Bugzilla bug {0} is open for html '
                            'data.'.format(bug_id)
                        )
                    self.hardwaremodel.update(name, test_data['name'])
                    self.assertIsNotNone(self.hardwaremodel.search(
                        test_data['name']))
                    name = test_data['name']  # for next iteration

    @run_only_on('sat')
    @tier1
    def test_positive_delete(self):
        """Deletes the Hardware-Model

        @feature: Hardware-Model - Positive delete

        @assert: Hardware-Model is deleted
        """
        with Session(self.browser) as session:
            for test_data in valid_hw_model_names():
                with self.subTest(test_data):
                    bug_id = test_data.pop('bugzilla', None)
                    if bug_id is not None and bz_bug_is_open(bug_id):
                        self.skipTest(
                            'Bugzilla bug {0} is open for html '
                            'data.'.format(bug_id)
                        )
                    make_hw_model(session, name=test_data['name'])
                    self.hardwaremodel.delete(test_data['name'])
