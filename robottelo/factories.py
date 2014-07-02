"""Factories for building and creating Foreman entities.

Factories serve as a fixtures replacement. Rather than creating an exhaustive,
static set of entities on a Foreman deployment and writing tests that use those
entities, factories allow tests to create minimal sets of objects when they're
actually needed: when each individual test is run.

Each class in this module is a factory for creating a single type of entity.
For example, the ``ModelFactory`` class is a factory for building and creating
"Model" entities and the ``HostFactory`` class is a factory for building and
creating "Host" entities.

For more information on factories, read about class :class:`Factory`. For
examples of factory usage, see module :mod:`tests.foreman.api.test_model_v2`.

"""
from fauxfactory import FauxFactory
from robottelo import entities, orm
import random


def _string_field():
    """Return a value suitable for a ``robottelo.orm.StringField``."""
    return FauxFactory.generate_string(
        'utf8',
        FauxFactory.generate_integer(1, 1000)
    )


def _is_required(field_type):
    """Tell whether ``field_type`` is required or not.

    :param robottelo.orm.Field field_type: A ``Field``, or one of its more
        specialized brethren.
    :return: ``True`` if ``field_type.options.required`` is set and ``True``.
        ``False`` otherwise.
    :rtype: bool

    """
    if field_type.options.get('required', False):
        return True
    return False


def _get_default_value(field_type):
    """Return a value for a field of type ``field_type``.

    This method is capable of accepting a wide variety of field types and
    generating a value for fields of that type. For example, if an instance of
    ``robottelo.orm.BooleanField`` is passed in, either ``True`` or ``False``
    is returned.

    The following ``robottelo.orm`` fields are supported:

    * ``BooleanField``
    * ``EmailField``
    * ``FloatField``
    * ``IntegerField``
    * ``IPAddressField``
    * ``MACAddressField``
    * ``OneToOneField``
    * ``StringField``

    :param robottelo.orm.Field field_type: A ``Field`` instance, or an instance
        of one of its more specialized brethren.
    :return: A value suitable for use in a field of type ``field_type``.
    :raises TypeError: If no strategy exists for generating a value of type
        ``field_type``.

    """
    if isinstance(field_type, orm.BooleanField):
        return FauxFactory.generate_boolean()
    elif isinstance(field_type, orm.EmailField):
        return FauxFactory.generate_email()
    elif isinstance(field_type, orm.FloatField):
        return random.random() * 10000
    elif isinstance(field_type, orm.IntegerField):
        return FauxFactory.generate_integer()
    elif isinstance(field_type, orm.IPAddressField):
        return FauxFactory.generate_ipaddr()
    elif isinstance(field_type, orm.MACAddressField):
        return FauxFactory.generate_mac()
    elif isinstance(field_type, orm.OneToOneField):
        return None
    elif isinstance(field_type, orm.StringField):
        return _string_field()
    else:
        raise TypeError(
            'There is no default strategy for populating fields of type '
            '{0}.'.format(field_type)
        )


class Factory(object):
    """A mechanism for creating new entities.

    This class provides a mechanism for creating new entities on a Foreman
    deployment. It can be used as-is or subclassed.

    By default, a ``Factory`` is fairly useless:

    >>> Factory().attributes()
    {}

    However, when paired with an ``Entity``, a ``Factory`` becomes much more
    useful. For example, you can ask it to generate values for all of
    :class:`robottelo.entities.Model`'s required fields:

    >>> from robottelo.entities import Model
    >>> attrs = Factory(Model).attributes()
    >>> isinstance(attrs, dict)
    True
    >>> len(attrs.keys()) == 1
    True
    >>> 'name' in attrs.keys()
    True

    By default, ``Factory`` generates randomized values for required fields.
    However, you can provide exact values:

    >>> from robottelo.entities import Model
    >>> model_factory = Factory(Model)
    >>> model_factory.field_values['name'] = 'foo'
    >>> attrs = model_factory.attributes()
    >>> attrs['name'] == 'foo'
    True
    >>> attrs = model_factory.attributes(name='bar')
    >>> attrs['name'] == 'bar'
    True

    :class:`robottelo.entities.Model` has four fields, but only ``name`` is
    required. If you want an optional field:

    >>> from robottelo.entities import Model
    >>> attrs = Factory(Model).attributes(info='biz')
    >>> 'name' in attrs.keys() and 'info' in attrs.keys()
    True

    An ``Entity`` can define alternate names for its fields:

    >>> from robottelo.entities import Model
    >>> attrs = Factory(Model, 'API').attributes(info='biz')
    >>> 'model[name]' in attrs.keys() and 'model[info]' in attrs.keys()
    True

    Creating ``Factory`` objects from scratch can get repetitive, so you can
    create subclasses:

    >>> from robottelo.entities import Model
    >>> class MyModelFactory(Factory):
    ...     '''A "Model" factory with certain defaults set.'''
    ...     def __init__(self, interface=None):
    ...         super(MyModelFactory, self).__init__(
    ...             entities.Model,
    ...             interface=interface
    ...         )
    ...         field_values['name'] = 'foo'
    ...         field_values['info'] = 'bar'
    ...
    >>> attrs = MyModelFactory().attributes()
    >>> attrs['name'] == 'foo' and attrs['bar'] == 'bar'
    True
    >>> attrs = MyModelFactory().attributes(name='biz')
    >>> attrs['name'] == 'biz' and attrs['bar'] == 'bar'
    True
    >>> attrs = MyModelFactory('API').attributes()
    >>> attrs['model[name]'] == 'foo' and attrs['model[bar]'] == 'bar'
    True
    >>> attrs = MyModelFactory('API').attributes(name='biz')
    >>> attrs['model[name]'] == 'biz' and attrs['model[bar]'] == 'bar'
    True

    Finally, it should be possible to create dependent objects using the
    ``create`` method. However, this has not yet been implemented.

    """
    def __init__(self, entity=None, interface=None):
        """Record arguments for later use.

        Other methods such as ``attributes`` and ``create`` use this method's
        arguments when performing their jobs.

        :param robottelo.orm.Entity entity: A logical representation of a
            Foreman entity. The object passed in may be either a class or a
            class instance.
        :param str interface: ``None``, ``'API'`` or ``'CLI'``. If not none,
            the keys produced by ``attributes``and ``create`` are customized.

        """
        # Check for invalid arguments
        interfaces = (None, 'API', 'CLI')
        if interface not in interfaces:
            raise ValueError(
                'Optional argument `interface` must be one of {0}, not '
                '{1}'.format(interfaces, interface)
            )

        # Everything seems to check out
        self.entity = entity
        self.interface = interface
        self.field_values = {}

    def _customize_field_names(self, fields):
        """Customize field names according to ``self.interface``.

        If ``self.interface`` indicates that this factory targets some
        particular Foreman interface, change the key names in ``fields``
        appropriately.

        If no interface is specified, ``_customize_field_names`` will return
        ``fields`` untouched. If an interface is specified and a corresponding
        attribute is set on ``self.entity.Meta``, customization is performed.
        If an interface is specified but no corresponding attribute is set, no
        customization is performed. For example:

        >>> from robottelo.factories import Factory
        >>> from robottelo import orm
        >>> class Commodity(orm.Entity):
        ...     '''A sample entity.'''
        ...     name = orm.StringField(required=True)
        ...     cost = orm.IntegerField(required=True)
        ...     class Meta(object):
        ...         '''Alternate names for this entity's fields.'''
        ...         api_names = {'name': 'commodity[name]'}
        ...         cli_names = {'cost': 'commodity[cost]'}
        ...
        >>> attrs = Factory(Commodity).attributes()
        >>> 'name' in attrs and 'cost' in attrs
        True
        >>> attrs = Factory(Commodity, 'API').attributes()
        >>> 'commodity[name]' in fields and 'cost' in fields
        True
        >>> attrs = Factory(Commodity, 'CLI').attributes()
        >>> 'name' in fields and 'commodity[cost]' in fields
        True

        :param dict fields: A dict mapping ``str`` names to ``robottelo.orm``
            fields.
        :return: ``fields``, but with updated keys.
        :rtype: dict

        """
        # The `fields` arg is often missing many {'name': orm.SomeType} pairs,
        # because non-required fields are typically removed before this method
        # is called. Thus, `pop` must be wrapped in a `try` block.

        if self.interface is 'API' and hasattr(self.entity.Meta, 'api_names'):
            for generic_name, api_name in self.entity.Meta.api_names.items():
                try:
                    fields[api_name] = fields.pop(generic_name)
                except KeyError:
                    pass

        elif (self.interface is 'CLI'
              and hasattr(self.entity.Meta, 'cli_names')):
            for generic_name, cli_name in self.entity.Meta.cli_names.items():
                try:
                    fields[cli_name] = fields.pop(generic_name)
                except KeyError:
                    pass

        return fields

    def attributes(self, **kwargs):
        """Return values for populating a new entity.

        When this method is called, no entity is created on a Foreman server.
        Instead, a dict is returned, and the information in that dict can be
        used to create an entity manually. Each dict key represents a field
        name, and each key can be used to access a corresponding field value.

        For entity attributes that point to dependent entities, a value of
        ``None`` is placed in the dictionary. For example::

            >>> host_attrs = HostFactory().attributes()
            >>> host_attrs['environment_id']
            None

        :return: Information for creating a new entity.
        :rtype: dict

        """
        entity_fields = self.entity.get_fields()  # source
        fields = {}                               # destination

        # Provide default values for fields, if appropriate.
        for name, type_ in entity_fields.items():
            if (
                not _is_required(type_) or
                name in kwargs or
                name in self.field_values
            ):
                continue
            fields[name] = _get_default_value(type_)

        # Use values from `self.field_values`, if appropriate.
        for name, value in self.field_values.items():
            if name in kwargs:
                continue
            fields[name] = value

        # Deal with arguments of this sort:
        # SomeFactory().attributes(name='Alice')
        for name, value in kwargs.items():
            if name not in entity_fields.keys():
                raise ValueError(
                    'Entity {0} has no attribute named "{1}".'.format(
                        self.entity, name
                    )
                )
            fields[name] = value

        # If dealing with an API or CLI, field names may need to be tweaked.
        return self._customize_field_names(fields)

    def create(self, **kwargs):
        """Create a new entity, plus all of its dependent entities.

        Create an entity and all of its dependent entities, then return a dict
        of information about the newly created entity. Each field on the newly
        created entity is represented by a dict key, and that key can be used
        to access the value of that field.

        :return: Information about the newly created entity.
        :rtype: dict

        """
        # FIXME: implement this method.
        raise NotImplementedError


class HostFactory(Factory):
    """Factory for a "Host" entity."""
    def __init__(self, interface=None):
        super(HostFactory, self).__init__(entities.Host, interface)


class ModelFactory(Factory):
    """Factory for a "Model" entity."""
    def __init__(self, interface=None):
        super(ModelFactory, self).__init__(entities.Model, interface)


class OrganizationFactory(Factory):
    """Factory for a "Organization" entity."""
    def __init__(self, interface=None):
        super(OrganizationFactory, self).__init__(
            entities.Organization,
            interface
        )


class ProductFactory(Factory):
    """Factory for a "Product" entity."""
    def __init__(self, interface=None):
        super(ProductFactory, self).__init__(entities.Product, interface)
