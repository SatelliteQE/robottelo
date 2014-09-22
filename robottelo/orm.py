"""Module that define the model layer used to define entities"""
from fauxfactory import FauxFactory
from robottelo.api import client
from robottelo.common import helpers
import booby
import booby.fields
import booby.inspection
import booby.validators
import httplib
import importlib
import inspect
import random
import thread
import threading
import time
import urlparse


class TaskTimeout(Exception):
    """Indicates that a task did not finish before the timout limit."""


def _poll_task(task_id, poll_rate=5, timeout=180, auth=None):
    """Implement :meth:`robottelo.entities.ForemanTask.poll`.

    :meth:`robottelo.entities.ForemanTask.poll` calls this function, as does
    :class:`robottelo.orm.EntityDeleteMixin`. Other mixins which have yet to be
    implemented, such as ``EntityCreateMixin``, may also call this function.

    This function has been placed in this module to keep the import tree sane.
    This function could also be placed in ``robottelo.api.utils``. However,
    doing so precludes :mod:`robottelo.api.utils` from importing
    :mod:`robottelo.entities`, which may be desirable in the future.

    This function is private because only entity mixins should use this.
    ``ForemanTask`` is, for obvious reasons, an exception.

    :raises robottelo.orm.TaskTimeout: when ``timeout`` expires

    """
    if auth is None:
        auth = helpers.get_server_credentials()

    # Implement the timeout.
    def raise_task_timeout():
        """Raise a KeyboardInterrupt exception in the main thread."""
        thread.interrupt_main()
    timer = threading.Timer(timeout, raise_task_timeout)

    # Poll until the task finishes. The timeout prevents an infinite loop.
    try:
        timer.start()

        path = '{0}/foreman_tasks/api/tasks/{1}'.format(
            helpers.get_server_url(),
            task_id
        )
        while True:
            response = client.get(path, auth=auth, verify=False)
            response.raise_for_status()
            task_info = response.json()
            if (task_info['result'] == 'success' or
                    task_info['result'] == 'error'):
                return task_info
            time.sleep(poll_rate)
    except KeyboardInterrupt:
        # raise_task_timeout will raise a KeyboardInterrupt when the timeout
        # expires. Catch the exception and raise TaskTimeout
        raise TaskTimeout("Timed out polling task {0}".format(task_id))
    finally:
        timer.cancel()


def _get_value(field, default):
    """Return a value for ``field``.

    Use the following strategies, in order, to find a value for ``field``:

    1. If ``field`` has a default value, return that value.
    2. If ``field`` provides choices, randomly return one of those choices.
    3. If ``default`` is callable, return ``default()``.
    4. Finally, fall back to returning ``default``.

    :param field: A :class:`Field`, or one of its more specialized brethren.
    :param default: A callable which yields a value.
    :return: A value appropriate for that field.

    """
    if 'default' in field.options.keys():
        return field.options['default']
    elif 'choices' in field.options.keys():
        return FauxFactory.generate_choice(field.options['choices'])
    elif callable(default):
        return default()
    else:
        return default


# -----------------------------------------------------------------------------
# Definition of individual entity fields. Wrappers for existing booby fields
# come first, and custom fields come second.
# -----------------------------------------------------------------------------


class BooleanField(booby.fields.Boolean):
    """Field that represents a boolean"""
    def get_value(self):
        """Return a value suitable for a :class:`BooleanField`."""
        return _get_value(self, FauxFactory.generate_boolean)


class EmailField(booby.fields.Email):
    """Field that represents an email"""
    def get_value(self):
        """Return a value suitable for a :class:`EmailField`."""
        return _get_value(self, FauxFactory.generate_email)


class FloatField(booby.fields.Float):
    """Field that represents a float"""
    def get_value(self):
        """Return a value suitable for a :class:`FloatField`."""
        return _get_value(self, random.random() * 10000)


class IntegerField(booby.fields.Integer):
    """Field that represents an integer"""
    def __init__(self, min_val=None, max_val=None, *args, **kwargs):
        self.min_val = min_val
        self.max_val = max_val
        super(IntegerField, self).__init__(*args, **kwargs)

    def get_value(self):
        """Return a value suitable for a :class:`IntegerField`."""
        return _get_value(
            self,
            FauxFactory.generate_integer(self.min_val, self.max_val)
        )


class StringField(booby.fields.String):
    """Field that represents a string."""
    def __init__(self, len=(1, 30), str_type=('utf8',), *args, **kwargs):
        """Constructor for a ``StringField``.

        The default ``len`` of string fields is short for two reasons:

        1. Foreman's database backend limits many fields to 255 bytes in
           length. As a result, ``len`` should be no longer than 85
           characters long, as 85 unicode characters may be up to 255 bytes
           long.
        2. Humans have to read through the error messages produced by
           Robottelo. Long error messages are hard to read through, and that
           hurts productivity. Thus, a ``len`` even shorter than 85 chars
           is desirable.

        :param len: Either a ``(min_len, max_len)`` tuple or an ``exact_len``
            integer.
        :param sequence str_type: The types of characters to generate when
            :meth:`get-value` is called. Any argument which can be passed to
            ``FauxFactory.generate_string`` can be provided in the sequence.

        """
        if isinstance(len, tuple):
            self.min_len, self.max_len = len
        else:
            self.min_len = self.max_len = len
        self.str_type = str_type
        super(StringField, self).__init__(*args, **kwargs)

    def get_value(self):
        """Return a value suitable for a :class:`StringField`."""
        return _get_value(
            self,
            lambda: FauxFactory.generate_string(
                FauxFactory.generate_choice(self.str_type),
                FauxFactory.generate_integer(self.min_len, self.max_len)
            )
        )


class Field(booby.fields.Field):
    """Base field class to implement other fields"""


class DateField(Field):
    """Field that represents a date"""


class DateTimeField(Field):
    """Field that represents a datetime"""


class DictField(Field):
    """Field that represents a set of key-value pairs."""
    def get_value(self):
        """Return a value suitable for a :class:`DictField`."""
        return _get_value(self, {})


class IPAddressField(StringField):
    """Field that represents an IP adrress"""
    def get_value(self):
        """Return a value suitable for a :class:`IPAddressField`."""
        return _get_value(self, FauxFactory.generate_ipaddr)


# FIXME: implement get_value()
class ListField(Field):
    """Field that represents a list of strings"""

    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__(
            booby.validators.List(booby.validators.String()),
            *args,
            **kwargs
        )


class MACAddressField(StringField):
    """Field that represents a MAC adrress"""
    def get_value(self):
        """Return a value suitable for a :class:`MACAddressField`."""
        return _get_value(self, FauxFactory.generate_mac)


class OneToOneField(Field):
    """Field that represents a reference to another entity."""
    def __init__(self, entity, *validators, **kwargs):
        self.entity = entity
        super(OneToOneField, self).__init__(*validators, **kwargs)

    def get_value(self):
        """Return an instance of the class that this field references."""
        return _get_class(self.entity)()


class OneToManyField(Field):
    """Field that represents a reference to zero or more other entities."""
    def __init__(self, entity, *validators, **kwargs):
        self.entity = entity
        super(OneToManyField, self).__init__(*validators, **kwargs)

    def get_value(self):
        """Return a set of instances of the class this field references.

        :return: An iterable of class instances.
        :rtype: list

        """
        return [_get_class(self.entity)()]


class URLField(StringField):
    """Field that represents an URL"""
    def get_value(self):
        """Return a value suitable for a :class:`URLField`."""
        return _get_value(self, FauxFactory.generate_url)


def _get_class(class_or_name, module='robottelo.entities'):
    """Return a class object.

    If ``class_or_name`` is a class, it is returned untouched. Otherwise,
    ``class_or_name`` is assumed to be a string. In this case, ``module`` is
    searched for a class by that name and returned.

    :param class_or_name: Either a class or the name of a class.
    :param str module: A dotted module name.
    :return: Either the class passed in or a class from ``module``.

    """
    if inspect.isclass(class_or_name):
        return class_or_name
    return getattr(importlib.import_module(module), class_or_name)


# -----------------------------------------------------------------------------
# Definition of parent Entity class and its dependencies.
# -----------------------------------------------------------------------------


class NoSuchPathError(Exception):
    """Indicates that the requested path cannot be constructed."""


class Entity(booby.Model):
    """A logical representation of a Foreman entity.

    This class is rather useless as is, and it is intended to be subclassed.
    Subclasses can specify two useful types of information:

    * fields
    * metadata

    Fields are represented by setting class attributes, and metadata is
    represented by settings attributes on the inner class named ``Meta``.

    """
    # The id() builtin is still available within instance methods, class
    # methods, static methods, inner classes, and so on. However, id() is *not*
    # available at the current level of lexical scoping after this point.
    id = IntegerField()  # pylint:disable=C0103

    class Meta(object):  # (too-few-public-methods) pylint:disable=R0903
        """Non-field information about this entity.

        This class is a convenient place to store any non-field information
        about an entity. For example, you can add the ``api_path`` and
        ``api_names`` variables. See :meth:`robottelo.orm.Entity.path` and
        :meth:`robottelo.factory.EntityFactoryMixin._factory_data` for
        details on the two variables, respectively.

        """

    def path(self, which=None):
        """Return the path to the current entity.

        Return the path to all entities of this entity's type if:

        * ``which`` is ``'all'``, or
        * ``which`` is ``None`` and instance attribute ``id`` is unset.

        Return the path to this exact entity if instance attribute ``id`` is
        set and:

        * ``which`` is ``'this'``, or
        * ``which`` is ``None``.

        Raise :class:`NoSuchPathError` otherwise.

        Child classes may choose to extend this method, especially if a child
        entity offers more than the two URLs supported by default. If extended,
        then the extending class should check for custom parameters before
        calling ``super``::

            def path(self, which):
                if which == 'custom':
                    return urlparse.urljoin(...)
                super(ChildEntity, self).__init__(which)

        This will allow the extending method to accept a custom parameter
        without accidentally raising a :class:`NoSuchPathError`.

        :param str which: Optional. Valid arguments are 'this' and 'all'.
        :return: A fully qualified URL.
        :rtype: str
        :raises robottelo.orm.NoSuchPathError: If no path can be built.

        """
        # (no-member) pylint:disable=E1101
        # It is OK that member ``self.Meta.api_path`` is not found. Subclasses
        # are required to set that attribute if they wish to use this method.
        #
        # Beware of leading and trailing slashes:
        #
        # urljoin('example.com', 'foo') => 'foo'
        # urljoin('example.com/', 'foo') => 'example.com/foo'
        # urljoin('example.com', '/foo') => '/foo'
        # urljoin('example.com/', '/foo') => '/foo'
        base = urlparse.urljoin(
            helpers.get_server_url() + '/',
            self.Meta.api_path
        )
        if which == 'all' or which is None and self.id is None:
            return base
        elif self.id is not None and (which is None or which == 'this'):
            return urlparse.urljoin(base + '/', str(self.id))
        raise NoSuchPathError

    @classmethod
    def get_fields(cls):
        """Return all defined fields as a dictionary.

        :return: A dictionary mapping ``str`` field names to ``robottelo.orm``
            field types.
        :rtype: dict

        """
        return booby.inspection.get_fields(cls)

    # FIXME: See GitHub issue #1082.
    def get_values(self):
        """Return all field values as a dictionary.

        All fields with a value of ``None`` are omitted from the returned dict.
        For example, if this entity is created::

            SomeEntity(name='foo', description=None)

        This dict is returned::

            {'name': 'foo'}

        This is a bug. See GitHub issue #1082.

        :return: A dictionary mapping field names to field values.
        :rtype: dict

        """
        fields = dict(self)
        for key, value in fields.items():
            if value is None:
                fields.pop(key)
        return fields


class EntityDeleteMixin(object):
    """A mixin that adds the ability to delete an entity."""
    # (too-few-public-methods) pylint:disable=R0903
    # It's OK that this class has only one public method. It's a targeted
    # mixin, not a standalone class.
    def delete(self, auth=None, synchronous=True):
        """Delete the current entity.

        Send an HTTP DELETE request to ``self.path(which='this')``.

        :param tuple auth: A ``(username, password)`` tuple used when accessing
            the API. If ``None``, the credentials provided by
            :func:`robottelo.common.helpers.get_server_credentials` are used.
        :param bool synchronous: What should happen if the server returns an
            HTTP 202 (accepted) status code? Wait for the task to complete if
            ``True``. Immediately return a task ID otherwise.
        :return: The ID of a :class:`robottelo.entities.ForemanTask` if an HTTP
            202 response was received. ``None`` otherwise.
        :raises: ``requests.exceptions.HTTPError`` if the response has an HTTP
            4XX or 5XX status code.
        :raises: ``ValueError`` If an HTTP 202 response is received and the
            response JSON can not be decoded.
        :raises robottelo.orm.TaskTimeout: If an HTTP 202 response is received,
            ``synchronous is True`` and the task times out.

        """
        # Delete this entity and check the status code of the response.
        if auth is None:
            auth = helpers.get_server_credentials()
        response = client.delete(
            self.path(which='this'),
            auth=auth,
            verify=False,
        )
        response.raise_for_status()

        # Return either a ForemanTask ID or None.
        if response.status_code is httplib.ACCEPTED:
            task_id = response.json()['id']
            if synchronous is True:
                _poll_task(task_id)
            return task_id
        return None


class EntityReadMixin(object):
    """A mixin that provides the ability to read an entity."""
    # (too-few-public-methods) pylint:disable=R0903
    # It's OK that this class has only one public method. It's a targeted
    # mixin, not a standalone class.
    def read_json(self, auth=None):
        """Get information about the current entity.

        Send an HTTP GET request to ``self.path(which='this')``. Return the
        decoded JSON response.

        :param tuple auth: A ``(username, password)`` tuple used when accessing
            the API. If ``None``, the credentials provided by
            :func:`robottelo.common.helpers.get_server_credentials` are used.
        :return: The server's response, with all JSON decoded.
        :rtype: dict
        :raises: ``requests.exceptions.HTTPError`` if the response has an HTTP
            4XX or 5XX status code.
        :raises: ``ValueError`` If the response JSON can not be decoded.

        """
        if auth is None:
            auth = helpers.get_server_credentials()
        response = client.get(
            self.path(which='this'),
            auth=auth,
            verify=False,
        )
        response.raise_for_status()
        return response.json()

    def read(self, auth=None, entity=None, attrs=None):
        """Instantiate and initialize an object of type ``type(self)``.

        Instantiate an object of type ``type(self)``. Populate the object's
        attributes using either ``attrs`` or
        :meth:`robottelo.orm.EntityReadMixin.read_json`. The ``attrs`` argument
        takes precedence.

        All of an entity's one-to-one and one-to-many relationships are
        populated with objects of the correct type. For example, if
        ``SomeEntity.other_entity`` is a one-to-one relationship, both of these
        commands should succeed:

            SomeEntity(id=N).read().other_entity.id
            SomeEntity(id=N).read().other_entity.read().other_attr

        In the example above, ``other_entity.id`` is the **only** attribute
        with a meaningful value. Calling ``other_entity.read`` populates the
        remaining entity attributes.

        :param tuple auth: Same as for
            :meth:`robottelo.orm.EntityReadMixin.read_json`.
        :param robottelo.orm.Entity entity: The entity to be populated and
            returned.
        :param dict attrs: Data used to populate the new entity's attributes.
        :return: An instance of type ``type(self)``. In other words, an
            instance of ``SomeEntity`` is returned if
            ``SomeEntity(id=N).read()`` is called.
        :rtype: robottelo.orm.Entity
        :raises: ``requests.exceptions.HTTPError`` if the response has an HTTP
            4XX or 5XX status code.

        """
        if entity is None:
            entity = type(self)()
        if attrs is None:
            attrs = self.read_json(auth=auth)

        # We must populate `entity`'s attributes from `attrs`.
        #
        # * OneToOneField names end with "_id"
        # * OneToManyField names end with "_ids"
        # * Other field names do not have any special name suffix.
        #
        # Well, that's the ideal. Unfortunately, the server often serves up
        # weirdly structured or incomplete data. (See BZ #1122267)
        for field_name, field_type in entity.get_fields().items():
            if isinstance(field_type, OneToOneField):
                # `OneToOneField.entity` may be either a class or a string. For
                # examples of this, look at a couple class definitions in
                # module `robottelo.entities`. `_get_class` returns a class.
                other_cls = _get_class(field_type.entity)
                entity_id = attrs[field_name + '_id']
                setattr(entity, field_name, other_cls(id=entity_id))
            elif isinstance(field_type, OneToManyField):
                other_cls = _get_class(field_type.entity)  # see above
                entity_ids = attrs[field_name + '_ids']
                setattr(
                    entity,
                    field_name,
                    [other_cls(id=entity_id) for entity_id in entity_ids]
                )
            else:
                setattr(entity, field_name, attrs[field_name])
        return entity
