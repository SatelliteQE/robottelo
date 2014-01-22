import copy
from robottelo.common.records.fields import convert_to_data

def intersection(first,other):
    if isinstance(first,Record):
        if not isinstance(other,Record):
            return False
        self_data = convert_to_data(first)
        other_data = convert_to_data(other)
        intersects = True
        for k in self_data:
            if k in other_data:
                self_v = self_data[k]
                other_v = other_data[k]
                intersects = intersects and intersection(self_v,other_v)
        return intersects
    elif type(first) == type([]):
        if not (type(other) == type([])):
            return False
        intersects = True
        for v in first:
            #at least one has to intersect
            intersects = intersects and any(intersection(v,i) for i in other)
        return intersects
    else:
        return first == other



class Options(object):
    def __init__(self, meta):
        # TODO: Add options default values
        self.fields = []
        self.meta = meta

    def contribute_to_class(self, cls, name):
        cls._meta = self
        self.model = cls

        if self.meta:
            for attr_name, value in self.meta.__dict__.items():
                setattr(self, attr_name, value)
        del self.meta

    def add_field(self, field):
        """Adds the field to self fields"""
        # TODO: we will need some aditional processing?
        self.fields.append(field)


class RecordBase(type):
    def __new__(cls, name, bases, attrs):
        super_new = super(RecordBase, cls).__new__

        # Ensure initialization is only performed for subclasses of Model
        # (excluding Model class itself).
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
    __metaclass__ = RecordBase

    def __init__(self, *args, **kwargs):
        fields_iter = iter(self._meta.fields)
        for val, field in zip(args, fields_iter):
            setattr(self, field.name, val)
            kwargs.pop(field.name, None)

        # Now we're left with the unprocessed fields that *must* come from
        # keywords, or default.

        for field in fields_iter:
            # is_related_object = False
            if kwargs:
                # TODO: detal with related objects, sample code commented below
                # if isinstance(field.rel, ForeignObjectRel):
                #     try:
                #         # Assume object instance was passed in.
                #         rel_obj = kwargs.pop(field.name)
                #         is_related_object = True
                #     except KeyError:
                #         try:
                #             # Object instance wasn't passed in -- must be an ID.
                #             val = kwargs.pop(field.attname)
                #         except KeyError:
                #             val = field.get_default()
                #     else:
                #         # Object instance was passed in. Special case: You can
                #         # pass in "None" for related objects if it's allowed.
                #         if rel_obj is None and field.null:
                #             val = None
                # else:
                try:
                    val = kwargs.pop(field.name)
                except KeyError:
                    val = field.get_default()
            else:
                val = field.get_default()

            setattr(self, field.name, val)

        # Process any property defined on model
        if kwargs:
            for prop in list(kwargs):
                try:
                    if isinstance(getattr(self.__class__, prop), property):
                        setattr(self, prop, kwargs.pop(prop))
                except AttributeError:
                    pass
            if kwargs:
                raise TypeError("'%s' is an invalid keyword argument for this function" % list(kwargs)[0])
        super(Record, self).__init__()

        # Checks if has a _post_init method and calls it to do additional
        # setup for this instance
        if hasattr(self, '_post_init'):
            self._post_init()

    def _string_data(self):
        return {k.__str__():
                    v._string_data() if isinstance(v,Record)
                        else [i.__str__() for i in v] if type(v) == type([])
                        else v.__str__()
                             for k,v in convert_to_data(self).items()}


    def __contains__(self,other):
        return intersection(other,self)

    def __str__(self):
        return self._string_data().__str__()

    def copy(self):
        return copy.deepcopy(self)
