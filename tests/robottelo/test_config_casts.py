"""Tests for module ``robottelo.config.casts``."""
import logging

from unittest2 import TestCase

from robottelo.config import casts


class BooleanTestCase(TestCase):
    def setUp(self):
        self.cast_boolean = casts.Boolean()

    def test_cast_true(self):
        self.assertTrue(all([
            self.cast_boolean(value)
            for value in ('1', 'yes', 'true', 'on', 'yEs', 'True', 'On')
        ]))

    def test_cast_false(self):
        self.assertFalse(any([
            self.cast_boolean(value)
            for value in ('0', 'no', 'false', 'off', 'No', 'False', 'OfF')
        ]))

    def test_cast_type(self):
        self.assertIsInstance(self.cast_boolean('true'), bool)

    def test_raise_value_error(self):
        with self.assertRaises(ValueError):
            self.cast_boolean('notaboolean')


class ListTestCase(TestCase):
    def setUp(self):
        self.cast_list = casts.List()

    def test_cast_list(self):
        self.assertEqual(
            self.cast_list('a, "b,c", d'),
            ['a', 'b,c', 'd']
        )

    def test_cast_type(self):
        self.assertIsInstance(self.cast_list('a,b,c'), list)


class TupleTestCase(TestCase):
    def setUp(self):
        self.cast_tuple = casts.Tuple()

    def test_cast_list(self):
        self.assertEqual(
            self.cast_tuple('a, "b,c", d'),
            ('a', 'b,c', 'd')
        )

    def test_cast_type(self):
        self.assertIsInstance(self.cast_tuple('a,b,c'), tuple)


class LoggingLevelTestCase(TestCase):
    def setUp(self):
        self.cast_logging_level = casts.LoggingLevel()

    def test_cast_logging_level(self):
        self.assertEqual([
            logging.CRITICAL,
            logging.DEBUG,
            logging.ERROR,
            logging.INFO,
            logging.WARNING,
        ], [
            self.cast_logging_level(value)
            for value in (
                'critical',
                'debug',
                'error',
                'info',
                'warning',
            )
        ])

    def test_raise_value_error(self):
        with self.assertRaises(ValueError):
            self.cast_logging_level('notalogginglevel')


class DictTestCase(TestCase):
    def setUp(self):
        self.cast_dict = casts.Dict()

    def test_cast_dict(self):
        self.assertEqual(
            self.cast_dict('a=1,"b=2,3,4",c=5'),
            {'a': '1', 'b': '2,3,4', 'c': '5'}
        )

    def test_cast_type(self):
        self.assertIsInstance(self.cast_dict('a=1,b=2,c=3'), dict)


class WebdriverDesiredCapabilitiesTestCase(TestCase):
    def setUp(self):
        self.cast_desired_capabilities = casts.WebdriverDesiredCapabilities()

    def test_cast_dict(self):
        self.assertEqual(
            self.cast_desired_capabilities('a=TruE,"b=2,3,4",c=FaLse'),
            {'a': True, 'b': '2,3,4', 'c': False}
        )

    def test_cast_type(self):
        self.assertIsInstance(self.cast_desired_capabilities('a=1'), dict)
