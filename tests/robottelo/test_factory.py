"""Tests for :mod:`robottelo.factory`."""
# (Too many public methods) pylint: disable=R0904
from fauxfactory import FauxFactory
from mock import Mock
from robottelo.api import client
from robottelo.common import conf
from robottelo import factory, orm
from unittest import TestCase


SAMPLE_FACTORY_NAME = 'christmahanakwanzika present'
SAMPLE_FACTORY_COST = 150


class SampleFactory(factory.Factory):
    """An example factory whose abstract methods have been implemented."""
    def _factory_path(self):
        """Return a path for creating a "Sample" entity."""
        return 'api/v2/samples'

    def _factory_data(self):
        """Return data for creating a "Sample" entity."""
        return {'name': SAMPLE_FACTORY_NAME, 'cost': SAMPLE_FACTORY_COST}


class MockResponse(object):  # (too-few-public-methods) pylint:disable=R0903
    """A mock ``requests.response`` object."""
    def json(self):  # (no-self-use) pylint:disable=R0201
        """A wrapper around method ``SampleFactory._factory_data``."""
        # (protected-access) pylint:disable=W0212
        return SampleFactory()._factory_data()


class MockErrorResponse(object):  # too-few-public-methods pylint:disable=R0903
    """A mock ``requests.response`` object."""
    def json(self):  # (no-self-use) pylint:disable=R0201
        """Return a simple error message.

        The error message returned by this method is similar to what might be
        returned by a real Foreman server.

        """
        return {'error': {'error name': 'error message'}}


class SampleEntityFactory(orm.Entity, factory.EntityFactoryMixin):
    """A class which is both an entity and a factory."""
    name = orm.StringField(required=True)
    label = orm.StringField()


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


class SampleFactoryTestCase(TestCase):
    """Tests for :class:`SampleFactory`.

    The public methods in :class:`robottelo.factory.Factory` can only be
    tested if certain private methods are overridden in subclasses. This test
    case uses a subclass which does just that.

    """
    def setUp(self):  # pylint:disable=C0103
        """Backup, customize and override objects."""
        self.client_post = client.post
        self.conf_properties = conf.properties.copy()
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

    def test_create(self):
        """Call ``create`` with no arguments. Receive a normal response.

        Assert that ``create`` returns the values contained in a (mock) server
        response.

        """
        client.post = Mock(return_value=MockResponse())
        self.assertEqual(MockResponse().json(), SampleFactory().create())

    def test_create_error(self):
        """Call ``create`` with no arguments. Receive an error response.

        Assert that ``create`` raises a :class:`robottelo.factory.FactoryError`
        if a (mock) server response contains an error message.

        """
        client.post = Mock(return_value=MockErrorResponse())
        with self.assertRaises(factory.FactoryError):
            SampleFactory().create()

    def test_create_auth(self):
        """Call ``create`` and specify the ``auth`` argument.

        Assert that the values provided for the ``auth`` argument are passed to
        :func:`robottelo.api.client.post`.

        """
        client.post = Mock(return_value=MockResponse())
        auth = (
            FauxFactory.generate_string('utf8', 10),  # username
            FauxFactory.generate_string('utf8', 10),  # password
        )
        SampleFactory().create(auth=auth)
        self.assertEqual(auth, client.post.call_args[1]['auth'])


class SampleEntityFactoryTestCase(TestCase):
    """Tests for :class:`SampleEntityFactory`."""
    # (protected-access) pylint:disable=W0212
    def test_implicit_fields(self):
        """
        Assert :meth:`robottelo.factory.EntityFactoryMixin._factory_data`
        returns only required fields.
        """
        attrs = SampleEntityFactory()._factory_data()
        self.assertIn('name', attrs.keys())
        self.assertNotIn('label', attrs.keys())

    def test_explicit_fields(self):
        """
        Assert :meth:`robottelo.factory.EntityFactoryMixin._factory_data`
        returns explicitly-specified values.
        """
        name = orm.StringField().get_value()
        label = orm.StringField().get_value()
        attrs = SampleEntityFactory(name=name, label=label)._factory_data()
        self.assertIn('name', attrs.keys())
        self.assertIn('label', attrs.keys())
        self.assertEqual(attrs['name'], name)
        self.assertEqual(attrs['label'], label)
