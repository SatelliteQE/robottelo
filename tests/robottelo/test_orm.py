"""Tests for robottelo.orm module"""
import unittest

from robottelo import orm


class SampleEntity(orm.Entity):
    """Sample entity to be used in the tests"""
    name = orm.StringField()
    value = orm.IntegerField()


class ManyRelatedEntity(orm.Entity):
    """An entity with a OneToManyField"""
    entities = orm.OneToManyField(SampleEntity)


class EntityTestCase(unittest.TestCase):
    def test_entity_get_fields(self):
        """Test Entity instance ``get_fields`` method."""
        entity = SampleEntity()
        fields = entity.get_fields()

        self.assertIn('name', fields)
        self.assertIn('value', fields)

        self.assertIsInstance(fields['name'], orm.StringField)
        self.assertIsInstance(fields['value'], orm.IntegerField)


class OneToManyFieldTestCase(unittest.TestCase):
    """Tests for the OneToManyField"""

    def test_value_is_single_model_instance(self):
        """Test a single entity value"""
        entity = SampleEntity(name='aname')
        other = ManyRelatedEntity(entities=entity)

        self.assertIsInstance(other.entities, list)
        self.assertEqual(other.entities[0].name, 'aname')

    def test_value_is_dictionary(self):
        """Test a single dictionary value"""
        entity = {'name': 'aname'}
        other = ManyRelatedEntity(entities=entity)

        self.assertIsInstance(other.entities, list)
        self.assertEqual(other.entities[0].name, 'aname')

    def test_value_is_list_of_dictionary(self):
        """Test a list of dictionaries value"""
        entity = [{'name': 'aname'}]
        other = ManyRelatedEntity(entities=entity)

        self.assertIsInstance(other.entities, list)
        self.assertEqual(other.entities[0].name, 'aname')
