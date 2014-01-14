"""Model's fields declarations"""

import rstr

from random import randint, choice


class Field(object):
    """Base class for all fields"""
    def __init__(self, required=False):
        self.name = None
        self.model = None
        self.required = required

    def convert_to_data():
        return value

    def generate(self):
        """Generate a random value for field"""
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

class ChoiceField(Field):
    def __init__(self, choices, **kwargs):
        super(ChoiceField, self).__init__(**kwargs)
        self.choices = choices

    def generate(self):
        return choice(self.choices)

def convert_to_data(instance):
    return {k:v for k,v in instance.__dict__.items() if (not k.startswith("_") and k!="")}

def load_from_data(instance,data):
    for k,v in data.items():
        instance.__dict__[k] = v
    return instance



