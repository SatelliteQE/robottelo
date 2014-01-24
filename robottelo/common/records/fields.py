"""Model's fields declarations"""

import rstr

from random import randint, choice
from robottelo.common.helpers import (
    generate_mac, generate_string, generate_ipaddr)


class NOT_PROVIDED:
    pass


class Field(object):
    """Base class for all fields"""

    def __init__(self, default=NOT_PROVIDED, required=False):
        self.default = default
        self.name = None
        self.record = None
        self.required = required

    def generate(self):
        """Generate a random value for field"""

        raise NotImplementedError(
            'A subclass should create a way to random generate this')

    def contribute_to_class(self, cls, name):
        """Method used to setup this field on the record"""

        if not self.name:
            self.name = name
        self.record = cls
        cls._meta.add_field(self)

    def has_default(self):
        """Returns a boolean of whether this field has a default value"""

        return self.default is not NOT_PROVIDED

    def get_default(self):
        """
        Returns the default value for this field.
        Otherwise generates a value if it is required else returns None
        """

        if self.has_default():
            if callable(self.default):
                return self.default()
            return self.default
        elif self.required:
            return self.generate()
        else:
            return None


class StringField(Field):
    def __init__(self, format=r'{record_name}_\d\d\d', maxlen=20,
                 str_type='xeger', **kwargs):
        super(StringField, self).__init__(**kwargs)
        self.format = format
        self.maxlen = maxlen
        self.str_type = str_type

    def _parse_field_format(self, fmt):
        """Parses the format provided and returns the parsed format"""
        return fmt.replace('{record_name}', self.record.__name__)

    def generate(self):
        if '{' in self.format:
            self.format = self._parse_field_format(self.format)
        if self.str_type == 'xeger':
            return rstr.xeger(self.format)[:self.maxlen]
        else:
            return generate_string(self.str_type, self.maxlen)


class IntegerField(Field):
    """Integer field that generates random values based on a range"""

    def __init__(self, min=1, max=10, **kwargs):
        super(IntegerField, self).__init__(**kwargs)
        self.min = min
        self.max = max

    def generate(self):
        return randint(self.min, self.max)


class MACField(Field):
    def __init__(self, delimiter=":", **kwargs):
        super(MACField, self).__init__(**kwargs)
        self.delimiter = delimiter

    def generate(self):
        return generate_mac(self.delimiter)


class ArrayField(Field):
    def __init__(self, delimiter=":", **kwargs):
        super(ArrayField, self).__init__(**kwargs)
        self.delimiter = delimiter

    def generate(self):
        return generate_mac(self.delimiter)


class IpAddrField(Field):
    def __init__(self, ip3=False, **kwargs):
        super(IpAddrField, self).__init__(**kwargs)
        self.ip3 = ip3

    def generate(self):
        return generate_ipaddr(self.ip3)


class ChoiceField(Field):
    def __init__(self, choices, **kwargs):
        super(ChoiceField, self).__init__(**kwargs)
        self.choices = choices

    def generate(self):
        return choice(self.choices)


class RelatedField(Field):
    def __init__(self, record_class, **kwargs):
        super(RelatedField, self).__init__(**kwargs)
        self.record_class = record_class

    def generate(self):
        return self.record_class()

class ManyRelatedFields(Field):
    """I have decided, that with [] it shall just set it,
       but with {"+":positive_diff,"-":negative_diff} it will update it"""
    def __init__(self, record_class, min, max, **kwargs):
        super(ManyRelatedFields, self).__init__(**kwargs)
        self.record_class = record_class

    def generate(self):
        i = randint(self.min, self.max)
        return [self.record_class() for i in range(1, x)]

def convert_to_data(instance):
    """Converts an instance to a data dictionary"""

    return {k: v for k, v in instance.__dict__.items()
            if (not k.startswith("_") and k!="")}

def convert_to_data(instance):
    """Converts an instance to a data dictionary"""

    return {k: v for k, v in instance.__dict__.items()
            if (not k.startswith("_") and k!="")}


def load_from_data(cls, data, transform_related = lambda instance_cls, data: args):
    """Loads instance attributes from a data dictionary"""
    instance = cls(CLEAN=True)
    related = {field.name : field for field in instance._meta.fields if isinstance(field, RelatedField)}
    data = transform_related(cls, data)
    for k, v in data.items():
        if k in related:
            related_class = related[k].record_class
            related_instance = load_from_data(related_class, v, transform_related)
            instance.__dict__[k] = related_instance
        else:
            instance.__dict__[k] = v
    return instance
