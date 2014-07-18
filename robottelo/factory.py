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
from robottelo.common.helpers import get_server_url, get_server_credentials
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
    * :meth:`Factory._unpack_response`

    A subclass may use :meth:`Factory.attributes` if it overrides
    :meth:`Factory._factory_data`. A subclass may also use
    :meth:`Factory.build` and :meth:`Factory.create` if it overrides
    :meth:`Factory._factory_path` (and sometimes
    :meth:`Factory._unpack_response` too).

    """
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

    # Pylint warns that `self` is unused. This is OK, as subclasses may use it.
    def _unpack_response(self, response):  # pylint:disable=R0201
        """Unpack the server's response after creating an entity.

        After sucessfully creating an entity on a server, a response is sent
        back. For example, after creating a "Model" entity::

            {u'model': {
                u'info': None, u'hosts_count': 0, u'name': u'foo',
                u'created_at': u'2014-07-07T16:06:23Z', u'updated_at':
                u'2014-07-07T16:06:23Z', u'hardware_model': None,
                u'vendor_class': None, u'id': 11
            }}

        The job of this method is to return information about the entity which
        was just created. In the example above, the inner dict should be
        returned.

        :param dict response: The data sent back from the server after creating
            an entity.
        :return: Information about the just-created entity.
        :rtype: dict

        """
        return response

    def attributes(self, fields=None):
        """Return values for populating a new entity.

        When this method is called, no entity is created on a Foreman server.
        Instead, a dict is returned, and the information in that dict can be
        used to manually create an entity at the path returned by
        :meth:`Factory._factory_path`. Within the dict of information returned,
        each dict key and value represent a field name and value, respectively.

        Fields can be given specific values:

        >>> from robottelo.entities import Product
        >>> attrs = Product().attributes(fields={'name': 'foo'})
        >>> attrs['name'] == 'foo'
        True

        If a dependent field is encountered, it is simply ignored:

        >>> from robottelo.entities import Product
        >>> attrs = Product().attributes()
        >>> 'organization_id' in attrs.keys()
        False

        :param dict fields: A dict mapping field names to exact field values.
        :return: Information for creating a new entity.
        :rtype: dict

        """
        # Start with values provided by user.
        if fields is None:
            fields = {}
        values = fields.copy()

        # Fetch remaining values from subclass and ignore FK fields.
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

    def build(self, fields=None):
        """Create dependent entities and return attributes for the current
        entity.

        Create all dependent entities, then return a dict of information that
        can be used to create an entity at the URL returned by
        :meth:`Factory._factory_path`.

        """
        # Use the values provided by the user.
        if fields is None:
            fields = {}
        values = fields.copy()

        # Populate all remaining required fields with values.
        # self._factory_data() returns field names and values, and there are
        # three types of values:
        #
        # * A Factory subclass. This is typically returned by
        #   OneToOneField.get_value(). We must call create() on this factory
        #   and get the created object's ID.
        # * A list of factory subclasses. This is typically returned by
        #   OneToManyField.get_value(). We must call create() on all of the
        #   factories in that list and collect all of their IDs.
        # * Some other type of value. We must use this value verbatim.
        #
        for name, value in self._factory_data().items():
            if name in values.keys():
                continue
            if isinstance(value, Factory):
                values[name] = value.create()['id']
            elif isinstance(value, list):
                values[name] = [factory.create()['id'] for factory in value]
            else:
                values[name] = value

        # We now have a dict of field names and values, which can be returned
        # to the caller.
        return values

    def create(self, fields=None):
        """Create a new entity, plus all of its dependent entities.

        Create an entity at the path returned by :meth:`Factory._factory_path`.
        If necessary, recursively create dependent entities. When done, return
        a dict of information about the newly created entity.

        :param dict fields: A dict mapping field names to field values.
        :return: Information about the newly created entity.
        :rtype: dict
        :raises robottelo.factory.FactoryError: If the server returns an error
            when attempting to create an entity.

        """
        # Create dependent entities and generate values for remaining fields.
        values = self.build(fields)

        # Create the current entity.
        path = urljoin(get_server_url(), self._factory_path())
        response = client.post(
            path,
            values,
            auth=get_server_credentials(),
            verify=False,
        ).json()
        if 'error' in response.keys() or 'errors' in response.keys():
            if 'error' in response.keys():
                message = response['error']
            else:
                message = response['errors']
            raise FactoryError(
                'Error encountered while POSTing to {0}. Error received: {1}'
                ''.format(path, message)
            )

        # Tell caller about created entity.
        return self._unpack_response(response)


class EntityFactoryMixin(Factory):
    """A mixin which allows an Entity to act as a Factory.

    Inserting this method into the class hierarchy of an
    :class:`robottelo.orm.Entity` allows that class to use all of the methods
    defined on :class:`robottelo.factory.Factory`, such as
    :meth:`Factory.attributes` and :meth:`Factory.create`.

    An :class:`robottelo.orm.Entity` which wishes to use this mixin must define
    the ``api_path`` attribute on its ``Meta`` class.

    """
    def _factory_path(self):
        """Return a path for creating the mixed-in entity."""
        return self.Meta.api_path[0]

    def _factory_data(self):
        """Return name-value pairs for each required field on the entity.

        This method does the following:

        1. Ask ``self.get_fields`` for a dict of field names and types. (see
           :meth:`robottelo.orm.Entity.get_fields`)
        2. Filter out all non-required fields.
        3. Change field names using ``self.Meta.api_names``, if present.
        4. Append the suffix '_id' and '_ids' to the name of each
           ``OneToOneField`` and ``OneTomanyField``, respectively.
        5. Generate values for each field.

        """
        # Step 1 and 2
        fields = {}
        for name, field in self.get_fields().items():
            if field_is_required(field):
                fields[name] = field

        # Step 3
        if hasattr(self.Meta, 'api_names'):
            fields = _copy_and_update_keys(fields, self.Meta.api_names)

        # Step 4
        for name, field in fields.items():
            if isinstance(field, orm.OneToOneField):
                fields[name + '_id'] = fields.pop(name)
            elif isinstance(field, orm.OneToManyField):
                fields[name + '_ids'] = fields.pop(name)

        # Step 5
        values = {}
        for name, field in fields.items():
            values[name] = field.get_value()

        return values
