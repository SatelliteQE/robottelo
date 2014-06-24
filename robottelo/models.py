"""Module that define the model layer used to define entities"""
import booby
import booby.fields


class Entity(booby.Model):
    """Entity class used to map system entities"""


# Wrappers for booby fields
class BooleanField(booby.fields.Boolean):
    """Field that represents a boolean"""


class EmailField(booby.fields.Email):
    """Field that represents a boolean"""


class Field(booby.fields.Field):
    """Base field class to implement other fields"""


class FloatField(booby.fields.Float):
    """Field that represents a float"""


class IntegerField(booby.fields.Integer):
    """Field that represents an integer"""


class StringField(booby.fields.String):
    """Field that represents a string"""


# Additional fields
class IPAddressField(StringField):
    """Field that represents an IP adrress"""


class MACAddressField(StringField):
    """Field that represents a MAC adrress"""


class OneToOneField(booby.fields.Embedded):
    """Field that represents a one to one related entity"""


class OneToManyField(OneToOneField):
    """Field that represents a one to many related entity"""


class URLField(StringField):
    """Field that represents an URL"""
