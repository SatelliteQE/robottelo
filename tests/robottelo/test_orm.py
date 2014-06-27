import unittest

from robottelo import orm


class SampleEntity(orm.Entity):
    """Entity class to be used on entities tests"""
    name = orm.StringField(required=True)
    cost = orm.IntegerField()


class EntityTestCase(unittest.TestCase):
    def test_entity_get_fields(self):
        """Test Entity instance ``get_fields`` method."""
        entity = SampleEntity()
        fields = entity.get_fields()

        self.assertIn('name', fields)
        self.assertIn('cost', fields)

        self.assertIsInstance(fields['name'], orm.StringField)
        self.assertIsInstance(fields['cost'], orm.IntegerField)
