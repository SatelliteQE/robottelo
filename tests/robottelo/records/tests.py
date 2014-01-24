import unittest

from .records import SampleRecord


class RecordsTestCase(unittest.TestCase):
    def setUp(self):
        self.record_class = SampleRecord

    def test_has_meta_attr(self):
        """Record has the _meta attr"""
        self.assertTrue(hasattr(self.record_class, '_meta'))

    def test_name_has_random_value(self):
        """Record instance generates a random value for a field"""
        instance = self.record_class()
        print instance.name
        self.assertTrue(
            instance.name.startswith(self.record_class.__name__))

    def test_can_set_name(self):
        """Can set a field attr value"""
        instance = self.record_class()
        instance.name = 'New Name'
        self.assertTrue(instance.name == 'New Name')

    def test_can_set_name_on_constructor(self):
        """Can set a field attr value on instantiation"""
        instance = self.record_class(name='New Name')
        self.assertTrue(instance.name == 'New Name')

    def test_field_default_value(self):
        """Field default value is used if value is not passed on constructor"""
        instance = self.record_class()
        self.assertEqual(instance.field_with_default, 'mydefault')
        instance = self.record_class(field_with_default='othervalue')
        self.assertEqual(instance.field_with_default, 'othervalue')

    def test_field_default_callable(self):
        """Field default value as callable is resolved"""
        instance = self.record_class()
        self.assertEqual(instance.callable_default, 'defaultfromcallable')

    def test_record_post_init_hook(self):
        """Post init is executed"""
        instance = self.record_class()
        self.assertTrue(hasattr(instance, 'post_init_var'))
