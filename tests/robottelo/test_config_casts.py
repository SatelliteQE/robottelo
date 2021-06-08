"""Tests for module ``robottelo.config.casts``."""
import pytest

from robottelo.config import casts


class TestBooleanCast:
    @pytest.fixture(scope='class')
    def cast_boolean(self):
        """An instance of casts.Boolean"""
        return casts.Boolean()

    def test_cast_true(self, cast_boolean):
        assert all(
            [cast_boolean(value) for value in ('1', 'yes', 'true', 'on', 'yEs', 'True', 'On')]
        )

    def test_cast_false(self, cast_boolean):
        assert not any(
            [cast_boolean(value) for value in ('0', 'no', 'false', 'off', 'No', 'False', 'OfF')]
        )

    def test_cast_type(self, cast_boolean):
        assert isinstance(cast_boolean('true'), bool)

    def test_raise_value_error(self, cast_boolean):
        with pytest.raises(ValueError):
            cast_boolean('notaboolean')


class TestListCast:
    @pytest.fixture(scope="class")
    def cast_list(self):
        return casts.List()

    def test_cast_list(self, cast_list):
        assert cast_list('a, "b,c", d') == ['a', 'b,c', 'd']

    def test_cast_type(self, cast_list):
        assert isinstance(cast_list('a,b,c'), list)


class TestTupleCast:
    @pytest.fixture(scope="class")
    def cast_tuple(self):
        return casts.Tuple()

    def test_cast_list(self, cast_tuple):
        assert cast_tuple('a, "b,c", d') == ('a', 'b,c', 'd')

    def test_cast_type(self, cast_tuple):
        assert isinstance(cast_tuple('a,b,c'), tuple)


class TestLoggingLevelCast:
    @pytest.fixture(scope="class")
    def cast_logging_level(self):
        return casts.LoggingLevel()

    def test_cast_logging_level(self, cast_logging_level):
        import logging

        assert [logging.CRITICAL, logging.DEBUG, logging.ERROR, logging.INFO, logging.WARNING] == [
            cast_logging_level(value) for value in ('critical', 'debug', 'error', 'info', 'warning')
        ]

    def test_raise_value_error(self, cast_logging_level):
        with pytest.raises(ValueError):
            cast_logging_level('notalogginglevel')


class TestDictCast:
    @pytest.fixture(scope="class")
    def cast_dict(self):
        return casts.Dict()

    def test_cast_dict(self, cast_dict):
        assert cast_dict('a=1,"b=2,3,4",c=5') == {'a': '1', 'b': '2,3,4', 'c': '5'}

    def test_cast_type(self, cast_dict):
        assert isinstance(cast_dict('a=1,b=2,c=3'), dict)


class TestWebdriverDesiredCapabilitiesCast:
    @pytest.fixture(scope="class")
    def cast_desired_capabilities(self):
        return casts.WebdriverDesiredCapabilities()

    def test_cast_dict(self, cast_desired_capabilities):
        assert cast_desired_capabilities('a=TruE,"b=2,3,4",c=FaLse') == {
            'a': True,
            'b': '2,3,4',
            'c': False,
        }

    def test_cast_type(self, cast_desired_capabilities):
        assert isinstance(cast_desired_capabilities('a=1'), dict)
