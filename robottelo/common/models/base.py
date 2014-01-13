"""Base models definition"""

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


class ModelBase(type):
    def __new__(cls, name, bases, attrs):
        super_new = super(ModelBase, cls).__new__

        # Ensure initialization is only performed for subclasses of Model
        # (excluding Model class itself).
        parents = [b for b in bases if isinstance(b, ModelBase) and
                not (b.__name__ == 'NewBase' and b.__mro__ == (b, object))]
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

class Model(object):
    __metaclass__ = ModelBase

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
                    val = field.generate()
            else:
                val = field.generate()

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
        super(Model, self).__init__()
