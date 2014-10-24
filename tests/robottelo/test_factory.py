"""Tests for :mod:`robottelo.factory`."""
# (Too many public methods) pylint: disable=R0904
from fauxfactory import gen_utf8
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


class SampleEntityFactory(orm.Entity, factory.EntityFactoryMixin):
    """A class which is both an entity and a factory."""
    name = orm.StringField(required=True)
    label = orm.StringField()


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
        # Make client.post(...).json() return {'foo': 'bar'}
        mock_response = Mock()
        mock_response.json.return_value = {'foo': 'bar'}
        client.post = Mock(return_value=mock_response)

        # Does create() return client.post(...).json()?
        self.assertEqual(SampleFactory().create(), {'foo': 'bar'})

    def test_create_auth(self):
        """Call ``create`` and specify the ``auth`` argument.

        Assert that the values provided for the ``auth`` argument are passed to
        :func:`robottelo.api.client.post`.

        """
        client.post = Mock()
        auth = (gen_utf8(10), gen_utf8(10))  # (username, password)
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
        name = gen_utf8()
        label = gen_utf8()
        attrs = SampleEntityFactory(name=name, label=label)._factory_data()
        self.assertIn('name', attrs.keys())
        self.assertIn('label', attrs.keys())
        self.assertEqual(attrs['name'], name)
        self.assertEqual(attrs['label'], label)
