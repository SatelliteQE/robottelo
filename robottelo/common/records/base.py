"""Records class definition with its options and metaclass"""

import copy
import itertools

from robottelo.common.records.fields import Field
from robottelo.common.records.fields import evaluate_choice


def create_choice(enum, fields):
    """Evaluates argument dictionaries to initialize a record object.
    >>> create_choice({"name":lambda :"n1"},{"label":"l1"})
    {'name': 'n1', 'label': 'l1'}
    """
    d = {k: evaluate_choice(v) for k, v in enum.items()}
    d.update({k: evaluate_choice(v) for k, v in fields.items()})
    return d


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


class Record(object):
    """ Entity definition and generating class
    """
    __metaclass__ = RecordBase

    def copy(self):
        """We use deepcopy as our copy implementation"""
        return copy.deepcopy(self)

    @classmethod
    def matrix_enumerate(cls, *args, **kwargs):
        """Calls enumerate with matrix option set to True.
        I believe that most of the time we shall use enumerate instead,
        passing MATRIX=True only when more thorough testing is required.
        """
        return cls.enumerate(MATRIX=True, *args, **kwargs)

    @classmethod
    def enumerate(cls, *args, **kwargs):
        """Generates instances of record so that
        every item in choice fields will be represented.
        If MATRIX=True, every combination of items in choice fields
        will be represented.

        I am utilizing keyword to make this function programable.
        I.e, most of the time, we might have tests with MATRIX=False,
        that results in sum(len(choices) for choices in choice_types),
        while with MATRIX=True it results in
        product(len(choices) for choices in choice_types)
        >>> from robottelo.common.records.base import Record
        >>> from robottelo.common.records import ChoiceField
        >>> class test(Record):
        ...      name = ChoiceField(["n1","n2","n3"])
        ...      label = ChoiceField(["l1","l2","l3"])
        ...      desc = ChoiceField(["d1","d2","d3"])
        ...      value = ChoiceField(["v1","v2","v3"])
        ...
        >>> len(test.enumerate())
        12
        >>> len(test.enumerate(MATRIX=True))
        81

        Now for some more concrete examples:
        >>> from robottelo.common.records.base import Record
        >>> from robottelo.common.records import ChoiceField
        >>> class test(Record):
        ...      name = ChoiceField(["n1","n2"])
        ...      desc = ChoiceField(["d1","d2"])
        ...
        >>> [(t.name,t.desc) for t in test.enumerate(MATRIX=True)]
        [('n1', 'd1'), ('n1', 'd2'), ('n2', 'd1'), ('n2', 'd2')]

        You can override arguments, either positionally,
        (here setting name to preset)
        >>> [(t.name,t.desc) for t in test.enumerate("preset")]
        [('preset', 'd1'), ('preset', 'd2')]

        You can override argument with keywords as well,
        (here setting desc to preset)
        >>> [(t.name,t.desc) for t in test.enumerate(desc="preset")]
        [('n1', 'preset'), ('n2', 'preset')]
        """

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
        """Constructs record based on its definition.
        Definition consists of class ineheriting from Record,
        that contains fields initialized to some of the
        robottelo.common.records.fields instances.

        In our example we shall use StringField.

        >>> from robottelo.common.records.base import Record
        >>> from robottelo.common.records import StringField
        >>> import re
        >>> class Test(Record):
        ...      name = StringField(format=r"abc{y,z}*")
        ...      number = StringField(str_type="numeric")
        ...

        On blank creation, each of the fields will be generated,
        based on the definition.
        >>> t = Test()
        >>> re.match(r"abc{y,z}*",t.name) != None
        True
        >>> t.number.isdigit()
        True

        You can set fields by positionall arguments
        >>> t = Test("name1","doesn't-check-validity")
        >>> t.name
        'name1'
        >>> t.number
        "doesn't-check-validity"

        You can set fields by keyword arguments
        >>> t = Test(number="123",name="name1")
        >>> t.name
        'name1'
        >>> t.number
        '123'

        If record fields have some specific requirements, you are
        able to set them up with _post_init private function

        >>> from robottelo.common.records import StringField
        >>> class Test(Record):
        ...      name = StringField(format=r"abc{y,z}*")
        ...      def _post_init(self):
        ...         self.label = self.name
        >>> t = Test(name='n1')
        >>> t.label
        'n1'


        Specifying Meta subclass will add _meta private field,
        that can contain various meta-infromation shared among
        the instances of record definition.

        I utilize it for visitor pattern in api implementation
        >>> class Test(Record):
        ...      name = StringField(format=r"abc{y,z}*")
        ...      number = StringField(str_type="numeric")
        ...
        ...      class Meta:
        ...         meta_data = "meta_information"
        ...
        >>> t = Test()
        >>> t._meta.meta_data
        'meta_information'

        Last feature is the ability to create blank record,
        while retaining the meta informaiton.
        >>> t = Test(blank_record=True)
        >>> hasattr(t, "name")
        False
        >>> t._meta.meta_data
        'meta_information'
        """

        blank = "blank_record" in kwargs and kwargs.pop("blank_record")

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

    def __str__(self):
        """For printout"""
        return "#"+self.__class__ + self.__dict__.__str__()

if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
