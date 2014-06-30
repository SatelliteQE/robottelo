"""Factories for building and creating Foreman entities.

Factories serve as a fixtures replacement. Rather than creating an exhaustive,
static set of entities on a Foreman deployment and writing tests that use those
entities, factories allow tests to create minimal sets of objects when they're
actually needed: when each individual test is run.

Each class in this module is a factory for creating a single type of entity.
For example, the ``ModelFactory`` class is a factory for building and creating
"Model" entities and the ``HostFactory`` class is a factory for building and
creating "Host" entities.

"""
from fauxfactory import FauxFactory
from robottelo import entities, orm


def _populate_string_field():
    """Return a value suitable for populating a string field."""
    return FauxFactory.generate_string(
        'utf8',
        FauxFactory.generate_integer(1, 1000)
    )


class Factory(object):
    """The parent class for all Factories.

    This class defines certain methods which are of use to all factories.

    """
    def __init__(self, entity=None, interface=None):
        """Record arguments for later use.

        Other methods such as ``attributes`` and ``create`` use this method's
        arguments when performing their jobs.

        :param robottelo.orm.Entity entity: A logical representation of a
            Foreman entity. The object passed in may be either a class or a
            class instance.
        :param str interface: ``None``, ``'API'`` or ``'CLI'``. A value other
            than ``None`` must be specified for ``build`` or ``create`` to
            function. The keys produced by ``attributes`` are customized if not
            ``None``.

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

    def _customize_field_names(self, fields):
        """Customize field names according to ``self.interface``.

        If ``self.interface`` indicates that this factory targets some
        particular Foreman interface, change the key names in ``fields``
        appropriately.

        If no interface is specified, ``_customize_field_names`` will return
        ``fields`` untouched. If an interface is specified and a corresponding
        attribute is set on ``self.entity.Meta``, customization is performed.
        If an interface is specified but no corresponding attribute is set, no
        customization is performed. For example::

            >>> class Commodity(orm.Entity):
            ...     '''A sample entity.'''
            ...     name = orm.StringField(required=True)
            ...     cost = orm.IntegerField()
            ...     class Meta(object):
            ...         '''Non-field information about this entity.'''
            ...         api_names = {'name': 'commodity[name]'}
            >>> factory = Factory(entity=Commodity)
            >>> fields = factory._customize_field_names(entity.get_fields())
            >>> 'name' in fields and 'cost' in fields
            True
            >>> factory = Factory(entity=Commodity, interface='API')
            >>> fields = factory._customize_field_names(entity.get_fields())
            >>> 'commodity[name]' in fields and 'cost' in fields
            True
            >>> factory = Factory(entity=Commodity, interface='CLI')
            >>> fields = factory._customize_field_names(entity.get_fields())
            >>> 'name' in fields and 'cost' in fields
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

        elif self.interface is 'CLI' \
                and hasattr(self.entity.Meta, 'cli_names'):
            for generic_name, cli_name in self.entity.Meta.cli_names.items():
                try:
                    fields[cli_name] = fields.pop(generic_name)
                except KeyError:
                    pass

        return fields

    def _get_required_fields(self):
        """Return ``self.entity``'s required fields.

        :return: A dictionary mapping ``str`` names to ``robottelo.orm``
            fields. Each name-field pair in the dictionary corresponds to one
            of ``self.entity``'s required fields.
        :rtype: dict

        """
        required_fields = {}
        for name, type_ in self.entity.get_fields().items():
            if type_.options.get('required', False):
                required_fields[name] = type_
        return required_fields

    def attributes(self):
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

        If an ``interface`` was specified when the factory was instantiated,
        attribute names are customized appropriately::

            >>> host_attrs = HostFactory(interface='API').attributes()
            >>> host_attrs['host[environment_id]']
            None

        :return: Information for creating a new entity.
        :rtype: dict

        """
        fields = {}
        for name, type_ in self._get_required_fields().items():
            # FIXME: Let child classes override this value generation logic.
            # FIXME: Provide more default _populate_* methods? Drop defaults?
            if isinstance(type_, orm.StringField):
                fields[name] = _populate_string_field()
            else:
                raise NotImplementedError
        return self._customize_field_names(fields)

    def create(self):
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
        super(HostFactory, self).__init__(entities.Host, interface=interface)


class ModelFactory(Factory):
    """Factory for a "Model" entity."""
    def __init__(self, interface=None):
        super(ModelFactory, self).__init__(entities.Model, interface=interface)
