"""Tests for module ``robottelo.factories``."""
# (Too many public methods) pylint: disable=R0904
from robottelo import factories, orm
from sys import version_info
from unittest import TestCase


class EmptyEntity(orm.Entity):
    """A sample entity which has no fields."""


class NonEmptyEntity(orm.Entity):
    """A sample entity which has fields."""
    name = orm.StringField(required=True)
    cost = orm.IntegerField()


class GetPopulateStringFieldTestCase(TestCase):
    """"Tests for method ``_populate_string_field``."""
    # (protected-access) pylint:disable=W0212
    def test_unicode(self):
        """Check whether a unicode string is returned."""
        string = factories._populate_string_field()
        if version_info[0] == 2:
            self.assertIsInstance(string, unicode)
        else:
            self.assertIsInstance(string, str)

    def test_len(self):
        """Check whether a string at least 1 char long is returned."""
        self.assertTrue(len(factories._populate_string_field()) > 0)


class FactoryTestCase(TestCase):
    """Tests for class ``Factory``."""
    def test__customize_field_names_v1(self):
        """Call ``_customize_field_names`` without altering ``Meta``.

        Create several factories using ``NonEmptyEntity`` and with
        ``interface`` set to default, ``'API'`` and ``'CLI'``. Ensure
        ``_customize_field_names`` produces correct output in each case.

        """
        # (protected-access) pylint:disable=W0212
        factory = factories.Factory(NonEmptyEntity)
        fields = factory._customize_field_names(NonEmptyEntity.get_fields())
        self.assertIn('name', fields)
        self.assertIn('cost', fields)

        factory = factories.Factory(NonEmptyEntity, 'API')
        fields = factory._customize_field_names(NonEmptyEntity.get_fields())
        self.assertIn('name', fields)
        self.assertIn('cost', fields)

        factory = factories.Factory(NonEmptyEntity, 'CLI')
        fields = factory._customize_field_names(NonEmptyEntity.get_fields())
        self.assertIn('name', fields)
        self.assertIn('cost', fields)

    def test__customize_field_names_v2(self):
        """Set attributes on ``Meta`` and call ``_customize_field_names``.

        Set ``NonEmptyEntity.Meta.api_names`` and
        ``NonEmptyEntity.Meta.cli_names``. Create several factories using
        ``NonEmptyEntity`` and with ``interface`` set to default, ``'API'`` and
        ``'CLI'``. Ensure ``_customize_field_names`` produces correct output in
        each case.

        """
        # (protected-access) pylint:disable=W0212
        NonEmptyEntity.Meta.api_names = {'name': 'customized'}
        NonEmptyEntity.Meta.cli_names = {'cost': 'field_names'}

        factory = factories.Factory(NonEmptyEntity)
        fields = factory._customize_field_names(NonEmptyEntity.get_fields())
        self.assertIn('name', fields)
        self.assertIn('cost', fields)

        factory = factories.Factory(NonEmptyEntity, 'API')
        fields = factory._customize_field_names(NonEmptyEntity.get_fields())
        self.assertIn('customized', fields)
        self.assertIn('cost', fields)

        factory = factories.Factory(NonEmptyEntity, 'CLI')
        fields = factory._customize_field_names(NonEmptyEntity.get_fields())
        self.assertIn('name', fields)
        self.assertIn('field_names', fields)

    def test__get_required_fields_v1(self):
        """Create a factory using ``EmptyEntity`` and call
        ``_get_required_fields``.

        """
        # (protected-access) pylint:disable=W0212
        self.assertEqual(
            factories.Factory(EmptyEntity)._get_required_fields(),
            {},
        )

    def test__get_required_fields_v2(self):
        """Create a factory using ``NonEmptyEntity`` and call
        ``_get_required_fields``.

        """
        # (protected-access) pylint:disable=W0212
        fields = factories.Factory(NonEmptyEntity)._get_required_fields()
        self.assertIn('name', fields)
        self.assertNotIn('cost', fields)
        self.assertIsInstance(fields['name'], orm.StringField)

    def test_attributes_v1(self):
        """Pass in ``EmptyEntity, then call ``attributes``.

        Assert an empty dict is returned.

        """
        self.assertEqual({}, factories.Factory(EmptyEntity).attributes())

    def test_attributes_v2(self):
        """Pass in ``NonEmptyEntity, then call ``attributes``.

        Assert the dict returned contains the correct keys, and that those keys
        correct to the correct datatypes.

        """
        attrs = factories.Factory(NonEmptyEntity).attributes()
        self.assertEqual(len(attrs.keys()), 1)
        self.assertIn('name', attrs)
        self.assertEqual(
            type(factories._populate_string_field()),  # pylint:disable=W0212
            type(attrs['name'])
        )
