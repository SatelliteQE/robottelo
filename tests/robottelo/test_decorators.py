"""Unit tests for :mod:`robottelo.decorators`."""
from unittest import mock

from unittest2 import SkipTest
from unittest2 import TestCase

from robottelo import decorators


class CacheableTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.cacheable`."""

    def setUp(self):
        self.object_cache_patcher = mock.patch.dict(
            'robottelo.decorators.OBJECT_CACHE')
        self.object_cache = self.object_cache_patcher.start()

        def make_foo(options):
            return {'id': 42}

        self.make_foo = decorators.cacheable(make_foo)

    def tearDown(self):
        self.object_cache_patcher.stop()

    def test_build_cache(self):
        """Create a new object and add it to the cache."""
        obj = self.make_foo(cached=True)
        self.assertEqual(decorators.OBJECT_CACHE, {'foo': {'id': 42}})
        self.assertEqual(id(decorators.OBJECT_CACHE['foo']), id(obj))

    def test_return_from_cache(self):
        """Return an already cached object."""
        cache_obj = {'id': 42}
        decorators.OBJECT_CACHE['foo'] = cache_obj
        obj = self.make_foo(cached=True)
        self.assertEqual(id(cache_obj), id(obj))

    def test_create_and_not_add_to_cache(self):
        """Create a new object and not add it to the cache."""
        self.make_foo(cached=False)
        self.assertNotIn('foo', decorators.OBJECT_CACHE)
        self.assertEqual(decorators.OBJECT_CACHE, {})


class SkipIfTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.skip_if`."""

    def test_raise_skip_test(self):
        """Skip a test method on True condition"""
        @decorators.skip_if(True)
        def dummy():
            pass

        with self.assertRaises(SkipTest):
            dummy()

    def test_execute_test_with_false(self):
        """Execute a test method on False condition"""
        @decorators.skip_if(False)
        def dummy():
            pass

        dummy()

    def test_raise_type_error(self):
        """Type error is raised with no condition (None) provided"""
        with self.assertRaises(TypeError):
            @decorators.skip_if()
            def dummy():
                pass

            dummy()

    def test_raise_default_message(self):
        """Test is skipped with a default message"""
        @decorators.skip_if(True)
        def dummy():
            pass

        try:
            dummy()
        except SkipTest as err:
            self.assertIn(
                'Skipping due expected condition is true',
                err.args
            )

    def test_raise_custom_message(self):
        """Test is skipped with a custom message"""
        @decorators.skip_if(True, 'foo')
        def dummy():
            pass

        try:
            dummy()
        except SkipTest as err:
            self.assertIn('foo', err.args)


class SkipIfNotSetTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.skip_if_not_set`."""

    def setUp(self):
        self.settings_patcher = mock.patch('robottelo.decorators.settings')
        self.settings = self.settings_patcher.start()
        self.settings.all_features = ['clients']

    def tearDown(self):
        self.settings_patcher.stop()

    def test_raise_skip_if_method(self):
        """Skip a test method if configuration is missing."""
        self.settings.clients.validate.side_effect = ['Validation error']

        @decorators.skip_if_not_set('clients')
        def dummy():
            pass

        with self.assertRaises(SkipTest):
            dummy()

    def test_raise_skip_if_setup(self):
        """Skip setUp method if configuration is missing."""
        self.settings.clients.validate.side_effect = ['Validation error']

        class MyTestCase(object):
            @decorators.skip_if_not_set('clients')
            def setUp(self):
                pass

        test_case = MyTestCase()
        with self.assertRaises(SkipTest):
            test_case.setUp()

    def test_raise_skip_if_setupclass(self):
        """Skip setUpClass method if configuration is missing."""
        self.settings.clients.validate.side_effect = ['Validation error']

        class MyTestCase(object):
            @classmethod
            @decorators.skip_if_not_set('clients')
            def setUpClass(cls):
                pass

        with self.assertRaises(SkipTest):
            MyTestCase.setUpClass()

    def test_not_raise_skip_if(self):
        """Don't skip if configuration is available."""
        self.settings.clients.validate.side_effect = [[]]

        @decorators.skip_if_not_set('clients')
        def dummy():
            return 'ok'

        self.assertEqual(dummy(), 'ok')

    def test_raise_value_error(self):
        """ValueError is raised when a misspelled feature is passed."""
        with self.assertRaises(ValueError):
            @decorators.skip_if_not_set('client')
            def dummy():
                pass

    def test_configure_settings(self):
        """Call settings.configure() if settings is not configured."""
        self.settings.clients.validate.side_effect = [[]]
        self.settings.configured = False

        @decorators.skip_if_not_set('clients')
        def dummy():
            return 'ok'

        self.assertEqual(dummy(), 'ok')
        self.settings.configure.called_once_with()


class StubbedTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.stubbed`."""

    @mock.patch('robottelo.decorators.unittest2.skip')
    def test_default_reason(self, skip):
        @decorators.stubbed()
        def foo():
            pass

        skip.assert_called_once_with(decorators.NOT_IMPLEMENTED)

    @mock.patch('robottelo.decorators.unittest2.skip')
    def test_reason(self, skip):
        @decorators.stubbed('42 is the answer')
        def foo():
            pass

        skip.assert_called_once_with('42 is the answer')
