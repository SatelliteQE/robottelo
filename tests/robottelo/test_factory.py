"""Tests for :mod:`robottelo.factory`."""
# (Too many public methods) pylint: disable=R0904
from fauxfactory import FauxFactory
from robottelo.api import client
from robottelo.common import conf
from robottelo import factory, orm
from unittest import TestCase


SAMPLE_FACTORY_NAME = 'christmahanakwanzika present'
SAMPLE_FACTORY_COST = 150


class SampleFactory(factory.Factory):
    """An example factory which overrides all four overridable methods."""
    def _factory_path(self):
        """Return a path for creating a "Sample" entity."""
        return 'api/v2/samples'

    def _factory_data(self):
        """Return a "Sample" entity's field names and types."""
        return {'name': SAMPLE_FACTORY_NAME, 'cost': SAMPLE_FACTORY_COST}

    def _unpack_response(self, response):
        """Unpack the server's response after creating an entity."""
        return response['sample']


class MockResponse(object):  # (too-few-public-methods) pylint:disable=R0903
    """A mock ``requests.response`` object."""
    def json(self):  # (no-self-use) pylint:disable=R0201
        """A stub method that returns the same data every time.

        :return: ``{'sample': SampleFactory()._factory_data()}``

        """
        # (protected-access) pylint:disable=W0212
        return {'sample': SampleFactory()._factory_data()}


class MockErrorResponse(object):  # too-few-public-methods pylint:disable=R0903
    """A mock ``requests.response`` object."""
    def json(self):  # (no-self-use) pylint:disable=R0201
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
    """Tests for :class:`robottelo.factory.Factory`."""
    # (protected-access) pylint:disable=W0212
    def test__factory_data(self):
        """Call :meth:`robottelo.factory.Factory._factory_data`.

        Ensure the method raises a ``NotImplementedError`` exception.

        """
        with self.assertRaises(NotImplementedError):
            factory.Factory()._factory_data()

    def test__factory_path(self):
        """Call :meth:`robottelo.factory.Factory._factory_path`.

        Ensure the method raises a ``NotImplementedError`` exception.

        """
        with self.assertRaises(NotImplementedError):
            factory.Factory()._factory_path()

    def test__unpack_response(self):
        """Call :meth:`robottelo.factory.Factory._unpack_response`.

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
        """Backup, customize and override objects."""
        self.client_post = client.post
        self.conf_properties = conf.properties
        conf.properties['main.server.hostname'] = 'example.com'
        conf.properties['foreman.admin.username'] = 'username'
        conf.properties['foreman.admin.password'] = 'password'

    def tearDown(self):  # pylint:disable=C0103
        """Restore backed-up objects."""
        client.post = self.client_post
        conf.properties = self.conf_properties

    # (protected-access) pylint:disable=W0212
    def test_attributes(self):
        """Call ``attributes`` with no arguments.

        Assert that the values provided by ``_factory_data`` are returned
        untouched.

        """
        self.assertEqual(
            SampleFactory()._factory_data(),
            SampleFactory().attributes()
        )

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

    def test_create(self):
        """Call ``create`` with no arguments.

        Assert that the values provided by ``MockResponse.json`` are unpacked
        and returned.

        """
        client.post = lambda url, data=None, **kwargs: MockResponse()
        self.assertEqual(
            SampleFactory()._factory_data(),  # See: MockResponse.json
            SampleFactory().create()
        )

    def test_create_error(self):
        """Call ``create`` with no arguments.

        Assert that, if an error is countered while creating an object, a
        :class:`robottelo.factory.FactoryError` is raised.

        """
        client.post = lambda url, data=None, **kwargs: MockErrorResponse()
        with self.assertRaises(factory.FactoryError):
            SampleFactory().create()
