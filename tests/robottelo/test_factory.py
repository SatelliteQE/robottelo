"""Tests for :mod:`robottelo.factory`."""
# (Too many public methods) pylint: disable=R0904
from fauxfactory import FauxFactory
from robottelo.common import conf
from robottelo import factory, orm
from unittest import TestCase


SAMPLE_FACTORY_NAME = 'christmahanakwanzika present'
SAMPLE_FACTORY_COST = 150


class SampleFactory(factory.Factory):
    """An example factory which overrides all four overridable methods."""
    def _get_path(self):
        """Return a path for creating a "Sample" entity."""
        return 'api/v2/samples'

    def _get_values(self):
        """Return a "Sample" entity's field names and types."""
        return {'name': SAMPLE_FACTORY_NAME, 'cost': SAMPLE_FACTORY_COST}

    def _get_field_names(self, fmt):
        """Return alternate field names for a "Sample"."""
        if fmt == 'api':
            return (('name', 'sample[name]'), ('cost', 'sample[cost]'))
        return tuple()

    def _unpack_response(self, response):
        """Unpack the server's response after creating an entity."""
        return response['sample']


class MockResponse(object):
    """A mock ``requests.response`` object."""
    def json(self):
        """A stub method that returns the same data every time.

        :return: ``{'sample': SampleFactory()._get_values()}``

        """
        # (protected-access) pylint:disable=W0212
        return {'sample': SampleFactory()._get_values()}


class MockErrorResponse(object):
    """A mock ``requests.response`` object."""
    def json(self):
        """A stub method that returns the same data every time.

        :return: ``{'error': {'error name': 'error message'}}``

        """
        return {'error': {'error name': 'error message'}}


class IsRequiredTestCase(TestCase):
    """Tests for :func:`robottelo.factory.field_is_required`."""
    # (protected-access) pylint:disable=W0212
    def test_field_is_required_v1(self):
        """Do not set the ``required`` attribute at all.

        Assert that :func:`robottelo.factory.field_is_required` returns
        ``False``.

        """
        self.assertFalse(factory.field_is_required(orm.Field()))

    def test_field_is_required_v2(self):
        """Set the ``required`` attribute to ``False``.

        Assert that :func:`robottelo.factory.field_is_required` returns
        ``False``.

        """
        self.assertFalse(factory.field_is_required(orm.Field(required=False)))

    def test_field_is_required_v3(self):
        """Set the ``required`` attribute to ``True``.

        Assert that :func:`robottelo.factory.field_is_required` returns
        ``True``.

        """
        self.assertTrue(factory.field_is_required(orm.Field(required=True)))


class CopyAndUpdateKeysTestCase(TestCase):
    """Tests for :func:`robottelo.factory._copy_and_update_keys`."""
    # (protected-access) pylint:disable=W0212
    def test_empty_args(self):
        """Provide empty values for ``somedict`` and ``mapping``."""
        self.assertEqual(
            {},
            factory._copy_and_update_keys({}, tuple())
        )

    def test_empty_somedict(self):
        """Provide an empty value for ``somedict``."""
        self.assertEqual(
            {},
            factory._copy_and_update_keys({}, (('foo', 'bar'), (1, 2)))
        )

    def test_empty_mapping(self):
        """Provide an empty value for ``mapping``."""
        self.assertEqual(
            {1: 2, 3: 4},
            factory._copy_and_update_keys({1: 2, 3: 4}, tuple())
        )

    def test_with_values(self):
        """Provide values for ``somedict`` and ``mapping``.

        Ensure that keys are updated correctly. Also, the output should be a
        copy of the input, so make sure that the input value does not change.

        """
        somedict = {1: 2, 3: 4}

        self.assertEqual(
            {0: 2, 3: 4},
            factory._copy_and_update_keys(somedict, ((1, 0),))
        )
        self.assertEqual({1: 2, 3: 4}, somedict)

        self.assertEqual(
            {0: 2, 'foo': 4},
            factory._copy_and_update_keys(somedict, ((1, 0), (3, 'foo')))
        )
        self.assertEqual({1: 2, 3: 4}, somedict)


class FactoryTestCase(TestCase):
    """Tests for class ``Factory``."""
    # (protected-access) pylint:disable=W0212
    def test__get_field_names(self):
        """Call ``_get_field_names``. Assert the method returns a tuple."""
        self.assertEqual(tuple(), factory.Factory()._get_field_names(None))

    def test__get_values(self):
        """Call ``_get_values``.

        Ensure the method raises a ``NotImplementedError`` exception.

        """
        with self.assertRaises(NotImplementedError):
            factory.Factory()._get_values()

    def test__get_path(self):
        """Call ``_get_path``.

        Ensure the method raises a ``NotImplementedError`` exception.

        """
        with self.assertRaises(NotImplementedError):
            factory.Factory()._get_path()

    def test__unpack_response(self):
        """Call ``_unpack_response``.

        Ensure the method returns the response untouched.

        """
        response = {'entity name': {'field name': 'field value'}}
        self.assertEqual(
            response,
            factory.Factory()._unpack_response(response)
        )


class SampleFactoryTestCase(TestCase):
    """Tests for :class:`SampleFactory`.

    The public methods in :class:`robottelo.factory.Factory` can only be
    tested if certain private methods are overridden in subclasses. This test
    case uses a subclass which does just that.

    """
    def setUp(self):  # pylint:disable=C0103
        """Insert several values into the global config."""
        conf.properties['main.server.hostname'] = 'example.com'
        conf.properties['foreman.admin.username'] = 'username'
        conf.properties['foreman.admin.password'] = 'password'

    # (protected-access) pylint:disable=W0212
    def test_attributes(self):
        """Call ``attributes`` with no arguments.

        Assert that the values provided by ``_get_values`` are returned
        untouched.

        """
        self.assertEqual(
            SampleFactory()._get_values(),
            SampleFactory().attributes()
        )

    def test_attributes_fmt(self):
        """Call ``attributes`` and specify the ``fmt`` argument.

        Use the ``fmt`` argument to ask for a variety of output formats.
        Assert that the key names returned are adjusted appropriately.

        """
        attrs = SampleFactory().attributes('no-op')
        self.assertIn('name', attrs.keys())
        self.assertIn('cost', attrs.keys())

        attrs = SampleFactory().attributes('api')
        self.assertIn('sample[name]', attrs.keys())
        self.assertIn('sample[cost]', attrs.keys())

    def test_attributes_fields(self):
        """Call ``attributes`` and specify the ``fields`` argument.

        Assert that the values provided via the ``fields`` argument override
        the default values generated.

        """
        name = FauxFactory.generate_string(
            'utf8',
            FauxFactory.generate_integer(1, 100)
        )
        self.assertEqual(
            {'name': name, 'cost': SAMPLE_FACTORY_COST},
            SampleFactory().attributes(fields={'name': name}),
        )

        cost = FauxFactory.generate_integer()
        self.assertEqual(
            {'name': name, 'cost': cost},
            SampleFactory().attributes(fields={'name': name, 'cost': cost}),
        )

        extra = FauxFactory.generate_boolean()
        self.assertEqual(
            {'name': name, 'cost': cost, 'extra': extra},
            SampleFactory().attributes(
                fields={'name': name, 'cost': cost, 'extra': extra}
            ),
        )

    def test_attributes_fmt_fields(self):
        """Call ``attributes`` and provide values for ``fmt`` and ``fields``.

        Assert that the values provided by ``fields`` are used and that key
        names are adjusted according to ``fmt``.

        """
        cost = FauxFactory.generate_integer()
        val = FauxFactory.generate_boolean()
        attrs = SampleFactory().attributes('api', {'cost': cost, 'val': val})

        self.assertIn('sample[name]', attrs.keys())
        self.assertIn('sample[cost]', attrs.keys())
        self.assertIn('val', attrs.keys())
        self.assertEqual(
            {
                'sample[name]': SAMPLE_FACTORY_NAME,
                'sample[cost]': cost,
                'val': val,
            },
            attrs
        )

    def test_create(self):
        """Call ``create`` with no arguments.

        Assert that the values provided by ``MockResponse.json`` are unpacked
        and returned.

        """
        factory._call_client_post = \
            lambda url, data, auth, verify: MockResponse()
        self.assertEqual(
            SampleFactory()._get_values(),  # See: MockResponse.json
            SampleFactory().create()
        )

    def test_create_error(self):
        """Call ``create`` with no arguments.

        Assert that, if an error is countered while creating an object, a
        :class:`robottelo.factory.FactoryError` is raised.

        """
        factory._call_client_post = \
            lambda url, data, auth, verify: MockErrorResponse()
        with self.assertRaises(factory.FactoryError):
            SampleFactory().create()

    def test_create_fmt(self):
        """Call ``create`` and specify the ``fmt`` argument.

        Assert that the response keys are formatted correctly.

        """
        factory._call_client_post = \
            lambda url, data, auth, verify: MockResponse()
        attrs = SampleFactory().create('api')
        self.assertIn('sample[name]', attrs.keys())
        self.assertIn('sample[cost]', attrs.keys())
