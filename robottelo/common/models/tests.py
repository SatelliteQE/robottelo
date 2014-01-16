import unittest

from robottelo.common import models


def default_value():
    return 'defaultfromcallable'


class OperatingSystem(models.Model):
    name = models.StringField(r"operatingsystem\d\d\d", required=True)
    major = models.IntegerField(required = True)
    minor = models.IntegerField(required = True)
    family = models.ChoiceField(
          ["Archlinux",
          "Debian",
          "Freebsd",
          "Gentoo",
          "Redhat",
          "Solaris",
          "Suse",
          "Windows"], required = True)
    release_name = models.StringField(r"osrelease\d\d\d", required = True)
    field_with_default = models.StringField(default='mydefault')
    callable_default = models.StringField(default=default_value)

    def _post_init(self):
        """Some post init processing"""
        setattr(self, 'post_init_var', True)

    class Meta:
        api_path = "/api/operatingsystems"
        api_json_key = u"operatingsystem"


class ModelsTestCase(unittest.TestCase):
    def setUp(self):
        self.model_class = OperatingSystem

    def test_has_meta_attr(self):
        """Model has the _meta attr"""
        self.assertTrue(hasattr(self.model_class, '_meta'))

    def test_name_has_random_value(self):
        """Model instance generates a random value for a field"""
        instance = self.model_class()
        self.assertTrue(
                instance.name.startswith(self.model_class.__name__.lower()))

    def test_can_set_name(self):
        """Can set a field attr value"""
        instance = self.model_class()
        instance.name = 'New Name'
        self.assertTrue(instance.name == 'New Name')

    def test_can_set_name_on_constructor(self):
        """Can set a field attr value on instantiation"""
        instance = self.model_class(name='New Name')
        self.assertTrue(instance.name == 'New Name')

    def test_field_default_value(self):
        """Field default value is used if value is not passed on constructor"""
        instance = self.model_class()
        self.assertEqual(instance.field_with_default, 'mydefault')
        instance = self.model_class(field_with_default='othervalue')
        self.assertEqual(instance.field_with_default, 'othervalue')

    def test_field_default_callable(self):
        """Field default value as callable is resolved"""
        instance = self.model_class()
        self.assertEqual(instance.callable_default, 'defaultfromcallable')

    def test_model_post_init_hook(self):
        """Post init is executed"""
        instance = self.model_class()
        self.assertTrue(hasattr(instance, 'post_init_var'))
