"""Records class definition with its options and metaclass"""

import copy
import itertools
from robottelo.common.records.fields import Field
import collections


def convert_to_data(instance):
    """Converts an instance to a data dictionary"""

    return {k: v for k, v in instance.__dict__.items()
            if (not k.startswith("_") and k != "")}


def evaluate_choice(chosen):
    if isinstance(chosen, Field):
        return chosen.generate()
    if isinstance(chosen, collections.Callable):
        return chosen.__call__()
    return chosen


class Options(object):
    """
    Option class for the records.
    Its instances will hold metadata for some record object
    """

    def __init__(self, meta):
        self.fields = []
        self.required_fields = []
        self.meta = meta
        self.record = None

    def contribute_to_class(self, cls, name):
        """Setups a options instance on the class"""

        cls._meta = self
        self.record = cls

        if self.meta:
            for attr_name, value in self.meta.__dict__.items():
                setattr(self, attr_name, value)
        del self.meta

    def add_field(self, field):
        """Adds the field to self fields"""

        self.fields.append(field)

        if field.required:
            self.required_fields.append(field)


class RecordBase(type):
    """Metaclass for Record class"""

    def __new__(cls, name, bases, attrs):
        super_new = super(RecordBase, cls).__new__

        # Ensure initialization is only performed for subclasses of Record
        # (excluding Record class itself).
        parents = [b for b in bases if isinstance(b, RecordBase)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        # Creates the class
        module = attrs.pop('__module__')
        new_class = super_new(cls, name, bases, {'__module__': module})
        attr_meta = attrs.pop('Meta', None)
        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta

        new_class.add_to_class('_meta', Options(meta))

        # Add all attributes to the class.
        for obj_name, obj in attrs.items():
            new_class.add_to_class(obj_name, obj)

        return new_class

    def add_to_class(cls, name, value):
        """
        Set attr with name and value to class.
        If the value has contribute_to_class method calls it instead of setattr
        """

        if hasattr(value, 'contribute_to_class'):
            value.contribute_to_class(cls, name)
        else:
            setattr(cls, name, value)


def create_choice(enum, fields):
    d = {k: evaluate_choice(v) for k, v in enum.items()}
    d.update({k: evaluate_choice(v) for k, v in fields.items()})
    return d


class Record(object):
    __metaclass__ = RecordBase

    def copy(self):
        return copy.deepcopy(self)

    @classmethod
    def matrix_enumerate(cls, *args, **kwargs):
        return enumerate(MATRIX=True)

    @classmethod
    def enumerate(cls, *args, **kwargs):
        matrix = True if "MATRIX" in kwargs and kwargs.pop("MATRIX") else False
        fnames = [f.name for f in iter(cls._meta.fields)]
        fields = dict(zip(fnames, args))
        fields.update({k: v for k, v in kwargs.items() if k in fnames})
        enumerated = {
            f.name: f.enumerate()
            for f in iter(cls._meta.fields)
            if f.enumerable and f.name not in fields
            }

        enumerated.update({
            k: v for k, v in fields.items()
            if isinstance(v, Field) and v.enumerable
            })

        fields = {
            k: v for k, v in fields.items()
            if not isinstance(v, Field) or not v.enumerable
            }

        e2 = []
        if matrix:
            e2 = [
                dict(zip(enumerated.keys(), y))
                for y in [x for x in itertools.product(*enumerated.values())]
                ]
        else:
            e2 = [
                {k: v} for k, v in
                itertools.chain(*[
                    [(k, v) for v in vx]
                    for k, vx in enumerated.items()])
                ]

        return [cls(**create_choice(enum, fields)) for enum in e2]

    def __init__(self, *args, **kwargs):

        blank = "BLANK" in kwargs and kwargs.pop("BLANK")

        fields_iter = iter(self._meta.fields)
        for val, field in zip(args, fields_iter):
            setattr(self, field.name, val)
            kwargs.pop(field.name, None)

        # Now we're left with the unprocessed fields that *must* come from
        # keywords, or default.

        for field in fields_iter:
            if kwargs:
                try:
                    val = kwargs.pop(field.name)
                except KeyError:
                    val = field.get_default()
            else:
                val = field.get_default() if not blank else None
            if not blank:
                setattr(self, field.name, val)

        # Process any property defined on record
        if kwargs:
            for prop in list(kwargs):
                try:
                    if isinstance(getattr(self.__class__, prop), property):
                        setattr(self, prop, kwargs.pop(prop))
                except AttributeError:
                    pass
            if kwargs:
                raise TypeError(
                    "'%s' is an invalid keyword argument for this function"
                    % list(kwargs)[0])
        super(Record, self).__init__()

        # Checks if has a _post_init method and calls it to do additional
        # setup for this instance
        if hasattr(self, '_post_init'):
            if not blank:
                post_init = getattr(self, '_post_init')
                post_init()

    def _string_data(self):
        return convert_to_data(self).items()

    def __str__(self):
        return self._string_data().__str__()
