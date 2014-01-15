"""Model's fields declarations"""

import rstr

from random import randint, choice
from robottelo.common.helpers import *

class Field(object):
    """Base class for all fields"""
    def __init__(self, value = None, required=False):
        self.name = None
        self.model = None
        self.required = required
        self.value = value

    def generate(self):
        """Generate a random value for field"""
        if self.value != None:
            return self.value
        raise NotImplementedError('A subclass should create a way to random generate this')

    def contribute_to_class(self, cls, name):
        """Method used to setup this field on the model"""
        if not self.name:
            self.name = name
        self.model = cls
        cls._meta.add_field(self)

class StringField(Field):
    def __init__(self, format=r'{model_name}_\d\d\d', maxlen=20, **kwargs):
        super(StringField, self).__init__(**kwargs)
        self.format = format
        self.maxlen = maxlen

    def _parse_field_format(self, fmt):
        """Parses the format provided and returns the parsed format"""
        return fmt.replace('{model_name}', self.model.__name__)

    def generate(self):
        if self.value != None:
            return self.value

        if self.required:
            if '{' in self.format:
                self.format = self._parse_field_format(self.format)
            return rstr.xeger(self.format)[:self.maxlen]
        else:
            return None

class IntegerField(Field):
    def __init__(self, min=1, max=10, **kwargs):
        super(IntegerField, self).__init__(**kwargs)
        self.min = min
        self.max = max

    def generate(self):
        return randint(self.min, self.max)

class MACField(Field):
    def __init__(self, delimiter=":", **kwargs):
        super(IntegerField, self).__init__(**kwargs)
        self.delimiter = delimiter
    def generate(self):
        return generate_mac(self.delimiter)

class ArrayField(Field):
    def __init__(self, delimiter=":", **kwargs):
        super(IntegerField, self).__init__(**kwargs)
        self.delimiter = delimiter
    def generate(self):
        return generate_mac(self.delimiter)

class IpAddrField(Field):
    def __init__(self, ip3=False, **kwargs):
        super(IntegerField, self).__init__(**kwargs)
        self.ip3 = ip3
    def generate(self):
        return generate_mac(self.ip3)

class ChoiceField(Field):
    def __init__(self, choices, **kwargs):
        super(ChoiceField, self).__init__(**kwargs)
        self.choices = choices

    def generate(self):
        if self.value != None:
            return self.value
        return choice(self.choices)

def convert_to_data(instance):
    return {k:v for k,v in instance.__dict__.items() if (not k.startswith("_") and k!="")}

def load_from_data(instance,data):
    for k,v in data.items():
        instance.__dict__[k] = v
    return instance

class RecordField(Field):
    def __init__(self, record_class, **kwargs):
        super(RecordField, self).__init__(**kwargs)
        self.record_class = record_class

    def generate(self):
        if self.value != None:
            return self.value
        return self.record_class()



