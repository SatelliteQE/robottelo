"""Base classes for creating factories.

Factories serve as a fixtures replacement. Rather than creating an exhaustive,
static set of entities on a Foreman deployment and writing tests that use those
entities, factories allow tests to create minimal sets of objects when they're
actually needed: when each individual test is run.

This module provides the base classes needed to implement factories. The
classes in this module are useless by themselves. For information on how to use
the base classes, read the docstrings on the classes themselves. For examples
of factory implementations, see :mod:`robottelo.entities`.

"""
from robottelo.api import client
from robottelo.common.helpers import (
    get_server_url, get_server_credentials
)
from robottelo import orm
from urlparse import urljoin


def _copy_and_update_keys(somedict, mapping):
    """Make a copy of ``somedict`` and update its keys with ``mapping``.

    ``mapping`` contains two-tuples, like this::

        ((1, 2), ('old_key', 'new_key'))

    This function examines each of the two-tuples in ``mapping``. The 1st
    two-tuple value is used as a key in the return value if the corresponding
    0th two-tuple value is used as a key in ``somedict``. For example:

    >>> _copy_and_update_keys({0: 5}, tuple())
    {0: 5}
    >>> _copy_and_update_keys({0: 5}, ((0, 1),))
    {1: 5}

    :param dict somedict: An arbitrary ``dict``.
    :param tuple mapping: A tuple containing two-tuples.
    :return: A copy of ``somedict``, but with updated keys.
    :rtype: dict

    """
    copy = somedict.copy()
    for old_key, new_key in mapping:
        if old_key in copy.keys():
            copy[new_key] = copy.pop(old_key)
    return copy


def field_is_required(field_type):
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


class FactoryError(Exception):
    """Indicates an error occurred while creating an entity."""


class Factory(object):
    """A mechanism for populating or creating Foreman entities.

    This class is useless as-is, and it should be subclassed. This class
    provides functionality that is common to all subclasses; client code can
    rely on the public functions exposed by this class.

    Subclasses are responsible for providing this class with certain pieces of
    information. Subclasses do that by overriding the following methods:

    * :meth:`Factory._factory_data`
    * :meth:`Factory._factory_path`

    A subclass may use :meth:`Factory.attributes` if it overrides
    :meth:`Factory._factory_data`. A subclass may also use
    :meth:`Factory.build` and :meth:`Factory.create` if it overrides
    :meth:`Factory._factory_path`.

    """
    @classmethod
    def _get_json_or_raise(cls, raw_response):
        try:
            response = raw_response.json()
        except ValueError as err:
            raise FactoryError(err.message, " instead: ", raw_response.text)

        if 'error' in response or 'errors' in response:
            message = response.get('error') or response.get('errors')
            raise FactoryError(
                'Error encountered while POSTing to {0}. '
                'Error received: {1} '
                'Status Code: {2} '
                ''.format(raw_response.url, message, raw_response.status_code)
            )

        return response

    def _factory_data(self):
        """Provide names and values for a Foreman entity's fields.

        This method describes a Foreman entity's fields. The description should
        be a dict mapping field names to values or factories. For example::

            {
                'name': 'Super Turbo-Charged Toupee-Destroyer',
                'manufacturer_id': ManufacturerFactory()
            }

        :return: Names and values for a Foreman entity's fields.
        :rtype: dict

        """
        raise NotImplementedError

    def _factory_path(self):
        """Provide an API path for creating a Foreman entity.

        :return: The path this factory will talk to when creating an entity.
            The path should be a path fragment, not be a fully qualified URL.
            For example, this is a valid return value:
            ``'api/v2/organizations'``.
        :rtype: str

        """
        raise NotImplementedError

    def attributes(self):
        """Return values for populating a new entity.

        When this method is called, no entity is created on a Foreman server.
        Instead, a dict is returned, and the information in that dict can be
        used to manually create an entity at the path returned by
        :meth:`Factory._factory_path`. Within the dict of information returned,
        each dict key and value represent a field name and value, respectively.

        If a dependent field is encountered, it is simply ignored:

        >>> from robottelo.entities import Product
        >>> attrs = Product().attributes()
        >>> 'organization_id' in attrs.keys()
        False

        :return: Information for creating a new entity.
        :rtype: dict

        """
        values = {}
        for name, value in self._factory_data().items():
            # `OneToOneField`s return a Factory instance.
            # `OneToManyField`s return a list of Factory instances.
            # Other field types return a value that can be used as-is.
            if (name in values.keys() or isinstance(value, Factory) or
                    isinstance(value, list)):
                continue
            values[name] = value

        # We now have a dict of field names and values, which can be returned
        # to the caller.
        return values

    def build(self, auth=None):
        """Create dependent entities and return attributes for the current
        entity.

        Create all dependent entities, then return a dict of information that
        can be used to create an entity at the URL returned by
        :meth:`Factory._factory_path`.

        For information about this method's parameters, return values and so
        on, see :meth:`Factory.create`.

        """
        # Populate all required fields with values.
        # self._factory_data() returns field names and values, and there are
        # three types of values:
        #
        # * A Factory subclass. In this case, we must call create() on the
        #   factory and get the created object's ID. (A factory subclass is
        #   often returned by OneToOneField.get_value().)
        # * A list of Factory subclasses and/or object IDs. For each item, we
        #   must call item.create() and get the created object's ID (in the
        #   case of a Factory subclass) or just use the given object ID as-is.
        #   (A list of factories and/or IDs is often returned by
        #   OneToManyField.get_value().)
        # * Some other type of value. We must use this value verbatim.
        #
        values = {}
        for name, value in self._factory_data().items():
            if name in values.keys():
                continue
            elif isinstance(value, Factory):
                values[name] = value.create(auth=auth)['id']
            elif isinstance(value, list):
                values[name] = [
                    (
                        factory_or_id.create(auth=auth)['id']
                        if isinstance(factory_or_id, Factory)
                        else factory_or_id
                    )
                    for factory_or_id
                    in value
                ]
            else:
                values[name] = value

        # We now have a dict of field names and values, which can be returned
        # to the caller.
        return values

    def create(self, auth=None):
        """Create a new entity, plus all of its dependent entities.

        Create an entity at the path returned by :meth:`Factory._factory_path`.
        If necessary, recursively create dependent entities. When done, return
        a dict of information about the newly created entity.

        :param tuple auth: A ``(username, password)`` pair to use when
            communicating with the API. If ``None``, the credentials returned
            by :func:`robottelo.common.helpers.get_server_credentials` are
            used.
        :return: Information about the newly created entity.
        :rtype: dict
        :raises robottelo.factory.FactoryError: If the server returns an error
            when attempting to create an entity.

        """
        if auth is None:
            auth = get_server_credentials()

        # Create dependent entities and generate values for non-FK fields.
        values = self.build(auth)

        # Create the current entity.
        path = urljoin(get_server_url(), self._factory_path())
        response = Factory._get_json_or_raise(
            client.post(path, values, auth=auth, verify=False))

        # Tell caller about created entity.
        return response


class EntityFactoryMixin(Factory):
    """A mixin which allows an Entity to act as a Factory.

    Inserting this method into the class hierarchy of an
    :class:`robottelo.orm.Entity` allows that class to use all of the methods
    defined on :class:`robottelo.factory.Factory`, such as
    :meth:`Factory.attributes` and :meth:`Factory.create`.

    An :class:`robottelo.orm.Entity` which wishes to use this mixin must ensure
    that its ``path()`` method functions correctly.

    """
    def _factory_path(self):
        """Return a path for creating the mixed-in entity."""
        return self.path()

    def _factory_data(self):
        """Return name-value pairs for each required field on the entity.

        This method follows the following logical steps:

        1. Ask ``self.get_fields`` for a dict of field names and types. (see
           :meth:`robottelo.orm.Entity.get_fields`)
        2. Filter out all non-required fields.
        3. Change field names using ``self.Meta.api_names``, if present.
        4. Append the suffix '_id' and '_ids' to the name of each
           ``OneToOneField`` and ``OneTomanyField``, respectively.
        5. Generate values for each field. If an explicit value was provided
           when the entity was created (e.g. `SomeFactory(name='foo')`), that
           is used instead.

        The actual method implementation differs from the above description.

        """
        values = self.get_values()  # explicit values provided by user
        fields = self.get_fields()  # fields from entity definition

        # When this loop is complete, `values` is complete. We just need to
        # adjust field names for Foreman.
        for name, field in fields.items():
            if name not in values.keys() and field_is_required(field):
                values[name] = field.get_value()

        # If self.Meta.api_names is present, then we must use it to transform
        # field names *before* appending _id and _ids to field names.
        if hasattr(self.Meta, 'api_names'):
            fields = _copy_and_update_keys(fields, self.Meta.api_names)
            values = _copy_and_update_keys(values, self.Meta.api_names)

        # Append _id and _ids to foreign key fields.
        for name in values.keys():
            if isinstance(fields[name], orm.OneToOneField):
                values[name + '_id'] = values.pop(name)
            elif isinstance(fields[name], orm.OneToManyField):
                values[name + '_ids'] = values.pop(name)

        return values


class EntitySearchFactoryMixin(EntityFactoryMixin):
    """For selectively adding query capabilities to EntityFactoryMixin."""

    def search(self, query={}):
        for attr in ['organization_id', 'name']:
            if attr in self.attributes():
                query.setdefault(attr, self.attributes()[attr])
        response = client.get(
            self.path(),
            auth=get_server_credentials(),
            verify=False,
            data=query
        )
        return EntitySearchFactoryMixin._get_json_or_raise(response)
