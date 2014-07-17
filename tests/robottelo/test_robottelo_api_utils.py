"""Unit tests for module ``robottelo.api.utils``."""
from fauxfactory import FauxFactory
from robottelo.api import utils
from sys import version_info
from unittest import TestCase


class MockResponse(object):
    """A mock ``requests.Response`` object."""
    def __init__(self):
        self.status_code = FauxFactory.generate_integer()


class StatusCodeErrorTestCase(TestCase):
    """Tests fore :func:`robottelo.api.utils.status_code_error`."""
    def setUp(self):
        self.path = FauxFactory.generate_string(
            'utf8',
            FauxFactory.generate_integer(min_value=1, max_value=100)
        )
        self.desired = FauxFactory.generate_integer()
        self.response = MockResponse()

    def test_no_json(self):
        """Make ``response.json()`` raise a ``ValueError``."""
        def json():
            raise ValueError()
        self.response.json = json
        msg = utils.status_code_error(self.path, self.desired, self.response)
        if version_info[0] == 2:
            self.assertIsInstance(msg, unicode)
        else:
            self.assertIsInstance(msg, str)

    def test_json(self):
        """Make ``response.json()`` return a dict with no error message."""
        self.response.json = lambda: {}
        msg = utils.status_code_error(self.path, self.desired, self.response)
        if version_info[0] == 2:
            self.assertIsInstance(msg, unicode)
        else:
            self.assertIsInstance(msg, str)

    def test_json_error(self):
        """Make ``response.json()`` return a dict with an error message."""
        self.response.json = lambda: {'error': 'error message'}
        msg = utils.status_code_error(self.path, self.desired, self.response)
        if version_info[0] == 2:
            self.assertIsInstance(msg, unicode)
        else:
            self.assertIsInstance(msg, str)
