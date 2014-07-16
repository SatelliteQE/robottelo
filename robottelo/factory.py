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

    Subclasses are responsible for describing a Foreman entity and its' fields.
    The public methods on this class (e.g. :meth:`Factory.attributes` or
    :meth:`Factory.create`) use that description to do their work.

    Subclasses may override the following methods:

    * :meth:`Factory._get_path`
    * :meth:`Factory._get_values`
    * :meth:`Factory._get_field_names`
    * :meth:`Factory._unpack_response`

    At a minimum, subclasses should override :meth:`Factory._get_values`. Read
    the docstrings on those methods for a full description of exactly what they
    do and should return.

    """
    def _get_values(self):
        """Provide names and values for a Foreman entity's fields.

        This method provides a description of a Foreman entity's fields. The
        description should be a dict mapping field names to values or
        factories. For example::

            {
                'name': 'Super Turbo-Charged Toupee-Destroyer',
                'manufacturer': ManufacturerFactory()
            }

        :return: Names and values for a Foreman entity's fields.
        :rtype: dict

        """
        raise NotImplementedError

    def _get_path(self):
        """Provide an API path for creating a Foreman entity.

        :return: The path this factory will talk to when creating an entity.
            The path should be a path fragment, not be a fully qualified URL.
            For example, this is a valid return value:
            ``'api/v2/organizations'``.
        :rtype: str

        """
        raise NotImplementedError

    # Pylint warns that both `fmt` and `self` are unused. This is OK, as
    # subclasses which override this method should and may use the argument,
    # respectively.
    def _get_field_names(self, fmt):  # pylint:disable=W0613,R0201
        """Provide alternative field names.

        This method should return an iterable of two-tuples. For example::

            (('old_key', 'new_key'), ('name', 'model[name]'))

        :param str fmt: An arbitrary label, such as ``'api'`` or ``'cli'``.
        :return: An iterable of two-tuples.
        :rtype: iterable

        """
        return tuple()

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

    def attributes(self, fmt=None, fields=None):
        """Return values for populating a new entity.

        When this method is called, no entity is created on a Foreman server.
        Instead, a dict is returned, and the information in that dict can be
        used to manually create an entity at the path returned by
        :meth:`Factory._get_path`. Within the dict of information returnd, each
        dict key and value represent a field name and value, respectively.

        Fields can be given specific values:

        >>> from robottelo.factories import ProductFactory
        >>> attrs = ProductFactory().attributes(fields={'name': 'foo'})
        >>> attrs['name'] == 'foo'
        True

        If a dependent field is encountered, it is simply ignored:

        >>> from robottelo.factories import ProductFactory
        >>> attrs = ProductFactory().attributes()
        >>> 'organization_id' in attrs.keys()
        False

        You can ask for field names to be customized just before they are
        returned:

        >>> from robottelo.factories import ModelFactory
        >>> attrs = ModelFactory().attributes()
        >>> 'name' in attrs
        True
        >>> attrs = ModelFactory().attributes(fmt='api')
        >>> 'model[name]' in attrs
        True

        :param str fmt: The desired format of the returned keys.
        :param dict fields: A dict mapping field names to exact field values.
        :return: Information for creating a new entity.
        :rtype: dict

        """
        # Start with values provided by user.
        if fields is None:
            fields = {}
        values = fields.copy()

        # Fetch remaining values from subclass and ignore FK fields.
        for name, value in self._get_values().items():
            # `OneToOneField`s return a Factory instance.
            # `OneToManyField`s return a list of Factory instances.
            # Other field types return a value that can be used as-is.
            if (name in values.keys() or isinstance(value, Factory) or
                    isinstance(value, list)):
                continue
            values[name] = value

        # Done generating field values.
        if fmt is not None:
            return _copy_and_update_keys(values, self._get_field_names(fmt))
        return values

    def build(self, fmt=None, fields=None):
        """Create dependent entities and return attributes for the current
        entity.

        Create all dependent entities, then return a dict of information that
        can be used to create an entity at the URL returned by
        :meth:`Factory._get_path`.

        """
        # Use the values provided by the user.
        if fields is None:
            fields = {}
        values = fields.copy()

        # Populate all remaining required fields with values.
        # self._get_values() returns field names and values, and there are
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
        for name, value in self._get_values().items():
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
        if fmt is not None:
            return _copy_and_update_keys(values, self._get_field_names(fmt))
        return values

    def create(self, fmt=None, fields=None):
        """Create a new entity, plus all of its dependent entities.

        Create an entity at the path returned by :meth:`Factory._get_path`. If
        necessary, recursively create dependent entities. When done, return a
        dict of information about the newly created entity.

        :param str fmt: The desired format of the returned keys.
        :param dict fields: A dict mapping field names to field values.
        :return: Information about the newly created entity.
        :rtype: dict
        :raises robottelo.factory.FactoryError: If the server returns an error
            when attempting to create an entity.

        """
        # Create dependent entities and generate values for remaining fields.
        values = self.build(fmt, fields)

        # Create the current entity. The Foreman API may not understand the
        # field names returned by _get_values(), so we use _get_field_names()
        # to perform a field name translation.
        path = urljoin(get_server_url(), self._get_path())
        response = client.post(
            path,
            _copy_and_update_keys(values, self._get_field_names('api')),
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
        response = self._unpack_response(response)
        if fmt is not None:
            return _copy_and_update_keys(response, self._get_field_names(fmt))
        return response


class EntityFactoryMixin(Factory):
    """A mixin which allows an Entity to act as a Factory.

    Inserting this method into the class hierarchy of an
    :class:`robottelo.orm.Entity` allows that class to use all of the methods
    defined on :class:`robottelo.factory.Factory`, such as
    :meth:`Factory.attributes` and :meth:`Factory.create`.

    An :class:`robottelo.orm.Entity` which wishes to use this mixin must define
    the ``api_path`` attribute on its ``Meta`` class.

    """
    def _get_path(self):
        """Return a path for creating the mixed-in entity."""
        return self.Meta.api_path[0]

    def _get_values(self):
        """Return name-value pairs for each required field on the entity."""
        values = {}
        # The base Entity class defines a `get_fields` method.
        for name, field in self.get_fields().items():
            if field_is_required(field):
                # `get_value` returns either a value or a Factory instance.
                values[name] = field.get_value()
        return values

    def _get_field_names(self, fmt):
        """Return alternate field names for a "Model"."""
        if fmt == 'api' and hasattr(self.Meta, 'api_names'):
            return self.Meta.api_names
        if fmt == 'cli' and hasattr(self.Meta, 'cli_names'):
            return self.Meta.cli_names
        else:
            return tuple()
