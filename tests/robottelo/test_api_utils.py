"""Unit tests for :mod:`robottelo.api.utils`."""
from robottelo.api import utils


def test_one_to_one_names():
    """Test :func:`robottelo.api.utils.one_to_one_names`."""
    assert utils.one_to_one_names('person') == {'person_name', 'person_id'}
