"""
Record's fields declarations

A field is responsible for handling the random generation of certain types of
data using its own attributes to control the data generation.

For example, an IntegerField represents an integer type of data and its
attributes control the range of numbers from which its value will be generated.

Each time that a record instance is created, the field value will be randomly
generated. Once you've created an instance of an IntegerField, subsequent
object creations will follow the same range determined previously.
"""

import rstr
import collections

from random import randint, choice
from robottelo.common.helpers import (
    generate_mac, generate_string, generate_ipaddr)
from robottelo.common.helpers import STR


def evaluate_choice(chosen):
    """Function used to allow choices to be callables and fields as well,
    not in ChoiceField, because I need to fake lazy evaluation for enumerate
    functionality.
    """
    if isinstance(chosen, Field):
        return chosen.generate()
    if isinstance(chosen, collections.Callable):
        return chosen.__call__()
    return chosen


class NOT_PROVIDED:
    pass


class Field(object):
    """
    Base class for all fields

    It defines the common attributes to all fields:

      * default: the default value, if defined, will be used every time a field
        value is requested. If not defined, the random generated value will be
        used. The default value could be a callable and will be called whenever
        a field value is necessary.
      * required: defines if a field is required or not. If the field is not
        required its value will be None when the default value is not defined
        otherwise will be used the default instead.

    The generate method should be overridden by a Field's subclass and should
    return a random generated value respecting the type of the field. Also
    the __init__ method could be overriden to add new attributes to control the
    value generation.

    Full example:

    class MyField(Field):
        def __init__(self, custom_arg='default for arg', **kwargs):
            # super should aways be called to ensure creation of field's
            # default attributes
            super(MyField, self).__init__(**kwargs)

            self.custom_arg = custom_arg

        def generate(self):
            if self.custom_arg == 'some expected value':
                return 'random value when some expected value is provided'
            else:
                return 'random value when some expected value is not provided'

    Each Field subclass should at least override the generate method and return
    a random value, otherwise a NotImplementedError will be raised.
    """

    def __init__(self, default=NOT_PROVIDED, required=True):
        self.default = default
        self.name = None
        self.record = None
        self.enumerable = False
        self.required = required

    def generate(self):
        """Override this method to generate a random value for field"""

        raise NotImplementedError(
            'A subclass should create a way to random generate a value')

    def contribute_to_class(self, cls, name):
        """Method used to setup this field on the Record class"""

        if not self.name:
            self.name = name
        self.record = cls
        cls._meta.add_field(self)

    def has_default(self):
        """Returns a boolean of whether this field has a default value"""

        return self.default is not NOT_PROVIDED

    def get_default(self):
        """
        Returns the default value for this field, even if the field is not
        required.
        Otherwise generates a value if it is required or returns None if not.
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
    """
    A Field subclass that represents the string type and generates random
    values based on the str_type attribute. The expected values to str_type
    are:

        * xeger: generates a random string based on a regex specified on the
          format field attribute. The default value is r'{record_name}_\d\d\d'.
          The {record_name} is a placeholder that will be replaced by the
          record class name. This str_type uses the rstr.xeger method which
          allows users to create a random string from a regular expression.
          For example, to generate a Canadian postal code, define the format
          as  r'[A-Z]\d[A-Z] \d[A-Z]\d' which would generate u'R6M 1W5'
        * alphanumeric: randomly generates alphanumeric strings
        * alpha: randomly generates alpha strings
        * numeric: randomly generates numeric strings
        * latin1: randomly generates latin1 encoded strings
        * utf8: randomly generates utf8 encoded strings
        * html: randomly generates a piece of HTML which have the format
          <tag>random string</tag>. In this case the maxlen controls the len of
          the tag content

    The maxlen attribute could be specified to limit the length of the
    generated string and defaults to 20.
    """

    def __init__(self, format=r'{record_name}_\d\d\d', maxlen=20,
                 str_type='xeger', **kwargs):
        super(StringField, self).__init__(**kwargs)
        self.format = format
        self.maxlen = maxlen
        self.str_type = str_type

    def _parse_field_format(self, fmt):
        """Replaces the expected placeholders with its value"""
        return fmt.replace('{record_name}', self.record.__name__)

    def generate(self):
        if '{' in self.format:
            self.format = self._parse_field_format(self.format)
        if self.str_type == 'xeger':
            return rstr.xeger(self.format)[:self.maxlen]
        else:
            return generate_string(self.str_type, self.maxlen)


class IntegerField(Field):
    """
    A Field subclass that represents the integer type and generates random
    value N such that min <= N <= max. The min defaults to 1 and max defaults
    to 10.
    """

    def __init__(self, min=1, max=10, **kwargs):
        super(IntegerField, self).__init__(**kwargs)
        self.min = min
        self.max = max

    def generate(self):
        return randint(self.min, self.max)


class MACField(Field):
    """
    A Field subclass that represents a MAC address type and generates random
    value in the format XX:XX:XX:XX:XX:XX where XX is a two digit hexadecimal
    value and : is the delimiter. The delimiter could be changed by defining
    the delimiter attribute which defaults to :.
    """

    def __init__(self, delimiter=":", **kwargs):
        super(MACField, self).__init__(**kwargs)
        self.delimiter = delimiter

    def generate(self):
        return generate_mac(self.delimiter)


class IpAddrField(Field):
    """
    A Field subclass that represents an IP address type and generates random
    value in the format NNN.NNN.NNN.NNN if ip3 attribute is False or in the
    format NNN.NNN.NNN.0 if ip3 attribute is True. The ip3 attribute defaults
    to False.
    """

    def __init__(self, ip3=False, **kwargs):
        super(IpAddrField, self).__init__(**kwargs)
        self.ip3 = ip3

    def generate(self):
        return generate_ipaddr(self.ip3)


class ChoiceField(Field):
    """
    A Field subclass that represents a choice from a sequence. The choices
    attribute should be defined to a non-empty sequence, or will will otherwise
    raise an IndexError exception. The value generated will be a random element
    from the choices sequence.
    """

    def __init__(self, choices, **kwargs):
        super(ChoiceField, self).__init__(**kwargs)
        self.choices = choices
        self.enumerable = True

    def generate(self):
        chosen = choice(self.choices)
        return evaluate_choice(chosen)

    def enumerate(self):
        """List all the possible values in this choice"""
        return self.choices


class RelatedField(Field):
    """
    A Field subclass that represents a related record type and creates a random
    related record instance using the related record class fields definition.
    This field eases the process of creating dependents records when creating a
    record. The record_class attributes should be defined by a Record subclass.
    """

    def __init__(self, record_class, **kwargs):
        super(RelatedField, self).__init__(**kwargs)
        self.record_class = record_class

    def generate(self):
        return self.record_class()


class ManyRelatedField(Field):
    """
    A Field subclass that represents a related record list type and creates
    a list of related record instances. The record_class attribute must be
    defined by a Record subclass and the min and max attributes controls the
    list length such that min <= length <= max. Every time a record instance is
    created a random value will be used to define the length of the list.
    """

    def __init__(self, record_class, min, max, **kwargs):
        super(ManyRelatedField, self).__init__(**kwargs)
        self.record_class = record_class
        self.min = min
        self.max = max

    def generate(self):
        number = randint(self.min, self.max)
        return [self.record_class() for i in range(number)]


def basic_positive(exclude=[], include=[]):
    """Often repeated field, that includes all the string types.
    Utilizing exclude and include to easily filter out types.
    """
    lst = [
        STR.alpha, STR.alphanumeric, STR.html,
        STR.latin1, STR.numeric, STR.utf8]

    if include:
        lst = include
    if exclude:
        lst = [i for i in lst if i not in exclude]

    return ChoiceField([
        StringField(str_type=i)
        for i in lst])
