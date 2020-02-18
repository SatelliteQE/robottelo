"""Unit tests for :mod:`robottelo.api.utils`."""
from unittest2 import TestCase

from robottelo.api import utils


class UtilsTestCase(TestCase):
    """Tests for the functions in :mod:`robottelo.api.utils`."""

    def test_one_to_one_names(self):
        """Test :func:`robottelo.api.utils.one_to_one_names`."""
        self.assertEqual(utils.one_to_one_names('person'), {'person_name', 'person_id'})

    def test_one_to_many_names(self):
        """Test :func:`robottelo.api.utils.one_to_many_names`."""
        self.assertEqual(utils.one_to_many_names('person'), {'person', 'person_ids', 'people'})
