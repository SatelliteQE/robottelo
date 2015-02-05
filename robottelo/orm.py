# -*- encoding: utf-8 -*-
"""Module that define the model layer used to define entities"""
from fauxfactory import gen_choice
from nailgun import client
from nailgun.entity_fields import (
    Field,
    _get_class,
    IntegerField,
    OneToManyField,
    OneToOneField,
)
from robottelo.common import helpers
import httplib
import thread
import threading
import time
import urlparse


#: Default for ``poll_rate`` argument to :func:`robottelo.orm._poll_task`.
TASK_POLL_RATE = 5
#: Default for ``timeout`` argument to :func:`robottelo.orm._poll_task`.
TASK_TIMEOUT = 180


class TaskTimeout(Exception):
    """Indicates that a task did not finish before the timout limit."""


def _poll_task(task_id, poll_rate=None, timeout=None, auth=None):
    """Implement :meth:`robottelo.entities.ForemanTask.poll`.

    See :meth:`robottelo.entities.ForemanTask.poll` for a full description of
    how this method acts. Other methods may also call this method, such as
    :meth:`robottelo.orm.EntityDeleteMixin.delete`.

    This function has been placed in this module to keep the import tree sane.
    This function could also be placed in :mod:`robottelo.api.utils`. However,
    doing so precludes :mod:`robottelo.api.utils` from importing
    :mod:`robottelo.entities`, which may be desirable in the future.

    This function is private because only entity mixins should use this.
    :class:`robottelo.entities.ForemanTask` is, for obvious reasons, an
    exception.

    """
    if poll_rate is None:
        poll_rate = TASK_POLL_RATE
    if timeout is None:
        timeout = TASK_TIMEOUT
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
            if task_info['state'] != 'running':
                return task_info
            time.sleep(poll_rate)
    except KeyboardInterrupt:
        # raise_task_timeout will raise a KeyboardInterrupt when the timeout
        # expires. Catch the exception and raise TaskTimeout
        raise TaskTimeout("Timed out polling task {0}".format(task_id))
    finally:
        timer.cancel()


# -----------------------------------------------------------------------------
# Definition of parent Entity class and its dependencies.
# -----------------------------------------------------------------------------


class NoSuchPathError(Exception):
    """Indicates that the requested path cannot be constructed."""


class NoSuchFieldError(Exception):
    """Indicates that the assigned-to :class:`Entity` field does not exist."""


class Entity(object):
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

    def __init__(self, **kwargs):
        fields = self.get_fields()
        for field_name, field_value in kwargs.items():
            if field_name not in fields:
                raise NoSuchFieldError(
                    '{0} is not a valid field. Valid fields are {1}.'
                    .format(field_name, ', '.join(fields.keys()))
                )
            setattr(self, field_name, field_value)

    class Meta(object):  # (too-few-public-methods) pylint:disable=R0903
        """Non-field information about this entity.

        This class is a convenient place to store any non-field information
        about an entity. For example, the ``api_path`` variable is used by
        :meth:`robottelo.orm.Entity.path`.

        """

    def path(self, which=None):
        """Return the path to the current entity.

        Return the path to base entities of this entity's type if:

        * ``which`` is ``'base'``, or
        * ``which`` is ``None`` and instance attribute ``id`` is unset.

        Return the path to this exact entity if instance attribute ``id`` is
        set and:

        * ``which`` is ``'self'``, or
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

        :param str which: Optional. Valid arguments are 'self' and 'base'.
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
        if which == 'base' or (which is None and 'id' not in vars(self)):
            return base
        elif (which == 'self' or which is None) and 'id' in vars(self):
            return urlparse.urljoin(base + '/', str(self.id))
        raise NoSuchPathError

    @classmethod
    def get_fields(cls):
        """Find all fields attributes of class ``cls``.

        :param cls: Any object. This method is only especially useful if that
            class has attributes that are subclasses of class ``Field``.
        :return: A dict mapping attribute names to ``Field`` objects.
        :rtype: dict

        """
        # When `dir` is called on "a type or class object, the list contains
        # the names of its attributes, and recursively of the attributes of its
        # bases." In constrast, `vars(cls)` returns only the attributes of
        # `cls` while ignoring all parent classes. Thus, this fails for child
        # classes:
        #
        #     for key, val in vars(cls).items():
        #         if isinstance(val, Field):
        #             attrs[key] = val
        #
        attrs = {}
        for field_name in dir(cls):
            field = getattr(cls, field_name)
            if isinstance(field, Field):
                attrs[field_name] = field
        return attrs


class EntityDeleteMixin(object):
    """A mixin that adds the ability to delete an entity."""

    def delete_raw(self, auth=None):
        """Delete the current entity.

        Send an HTTP DELETE request to :meth:`Entity.path`. Return the
        response. Do not check the response for any errors, such as an HTTP 4XX
        or 5XX status code.

        :param tuple auth: A ``(username, password)`` tuple used when accessing
            the API. If ``None``, the credentials provided by
            :func:`robottelo.common.helpers.get_server_credentials` are used.
        :return: A ``requests.response`` object.

        """
        if auth is None:
            auth = helpers.get_server_credentials()
        return client.delete(self.path(which='self'), auth=auth, verify=False)

    def delete(self, auth=None, synchronous=True):
        """Delete the current entity.

        Call :meth:`delete_raw` and check for an HTTP 4XX or 5XX response.
        Return either the JSON-decoded response or information about a
        completed foreman task.

        :param tuple auth: A ``(username, password)`` tuple used when accessing
            the API. If ``None``, the credentials provided by
            :func:`robottelo.common.helpers.get_server_credentials` are used.
        :param bool synchronous: What should happen if the server returns an
            HTTP 202 (accepted) status code? Wait for the task to complete if
            ``True``. Immediately return a response otherwise.
        :returns: Either the JSON-decoded response or information about a
            foreman task.
        :rtype: dict
        :raises: ``requests.exceptions.HTTPError`` if the response has an HTTP
            4XX or 5XX status code.
        :raises: ``ValueError`` If an HTTP 202 response is received and the
            response JSON can not be decoded.
        :raises robottelo.orm.TaskTimeout: If an HTTP 202 response is received,
            ``synchronous is True`` and the task times out.

        """
        response = self.delete_raw(auth)
        response.raise_for_status()
        if synchronous is True and response.status_code is httplib.ACCEPTED:
            return _poll_task(response.json()['id'], auth=auth)
        if response.status_code == httplib.NO_CONTENT:
            # "The server successfully processed the request, but is not
            # returning any content. Usually used as a response to a successful
            # delete request."
            return
        return response.json()


class EntityReadMixin(object):
    """A mixin that provides the ability to read an entity."""

    def read_raw(self, auth=None):
        """Get information about the current entity.

        Send an HTTP GET request to :meth:`Entity.path`. Return the response.
        Do not check the response for any errors, such as an HTTP 4XX or 5XX
        status code.

        :param tuple auth: A ``(username, password)`` tuple used when accessing
            the API. If ``None``, the credentials provided by
            :func:`robottelo.common.helpers.get_server_credentials` are used.
        :return: A ``requests.response`` object.

        """
        if auth is None:
            auth = helpers.get_server_credentials()
        return client.get(self.path(), auth=auth, verify=False)

    def read_json(self, auth=None):
        """Get information about the current entity.

        Call :meth:`read_raw`. Check the response status code, decode JSON and
        return the decoded JSON as a dict.

        :param tuple auth: Same as :meth:`read_raw`.
        :return: The server's response, with all JSON decoded.
        :rtype: dict
        :raises: ``requests.exceptions.HTTPError`` if the response has an HTTP
            4XX or 5XX status code.
        :raises: ``ValueError`` If the response JSON can not be decoded.

        """
        response = self.read_raw(auth)
        response.raise_for_status()
        return response.json()

    def read(self, auth=None, entity=None, attrs=None, ignore=()):
        """Get information about the current entity.

        Call :meth:`read_json`. Use this information to populate an object of
        type ``type(self)`` and return that object.

        All of an entity's one-to-one and one-to-many relationships are
        populated with objects of the correct type. For example, if
        ``SomeEntity.other_entity`` is a one-to-one relationship, this should
        return ``True``::

            isinstance(
                SomeEntity(id=N).read().other_entity,
                robottelo.orm.Entity
            )

        Additionally, both of these commands should succeed::

            SomeEntity(id=N).read().other_entity.id
            SomeEntity(id=N).read().other_entity.read().other_attr

        In the example above, ``other_entity.id`` is the **only** attribute
        with a meaningful value. Calling ``other_entity.read`` populates the
        remaining entity attributes.

        :param tuple auth: Same as :meth:`read_raw`.
        :param robottelo.orm.Entity entity: The object to be populated and
            returned. An object of type ``type(self)`` by default.
        :param dict attrs: Data used to populate the object's attributes. The
            response from ``read_json`` by default.
        :param tuple ignore: Attributes which should not be read from the
            server. This is mainly useful for attributes like a password which
            are not returned.
        :return: An instance of type ``type(self)``.
        :rtype: robottelo.orm.Entity

        """
        if entity is None:
            entity = type(self)()
        if attrs is None:
            attrs = self.read_json(auth=auth)

        # Rename fields using entity.Meta.api_names, if present.
        if hasattr(entity.Meta, 'api_names'):
            for local_name, remote_name in entity.Meta.api_names.items():
                attrs[local_name] = attrs.pop(remote_name)

        # We must populate `entity`'s attributes from `attrs`.
        #
        # * OneToOneField names end with "_id"
        # * OneToManyField names end with "_ids"
        # * Other field names do not have any special name suffix.
        #
        # Well, that's the ideal. Unfortunately, the server often serves up
        # weirdly structured or incomplete data. (See BZ #1122267)
        for field_name, field_type in entity.get_fields().items():
            if field_name in ignore:
                continue
            if isinstance(field_type, OneToOneField):
                # `OneToOneField.entity` may be either a class or a string. For
                # examples of this, look at a couple class definitions in
                # module `robottelo.entities`. `_get_class` returns a class.
                other_cls = _get_class(field_type.entity, 'robottelo.entities')
                entity_id = attrs[field_name + '_id']
                setattr(entity, field_name, other_cls(id=entity_id))
            elif isinstance(field_type, OneToManyField):
                other_cls = _get_class(field_type.entity, 'robottelo.entities')
                entity_ids = attrs[field_name + '_ids']
                setattr(
                    entity,
                    field_name,
                    [other_cls(id=entity_id) for entity_id in entity_ids]
                )
            else:
                setattr(entity, field_name, attrs[field_name])
        return entity


class EntityCreateMixin(object):
    """A mixin that provides the ability to create an entity.

    The methods provided by this mixin work together to create an entity. A
    typical tree of method calls looks like this::

        create
        └── create_json
            └── create_raw
                ├── create_missing
                └── create_payload

    Only :meth:`create_raw` communicates with the server.

    """

    def create_missing(self, auth=None):
        """Automagically populate all required instance attributes.

        Iterate through the set of all required class ``Field`` defined on
        ``type(self)`` and create a corresponding instance attribute if none
        exists. Subclasses should override this method if there is some
        relationship between two required fields.

        :param tuple auth: Same as :meth:`create_raw`.
        :return: Nothing. This method relies on side-effects.

        """
        for field_name, field in self.get_fields().items():
            if field.required and field_name not in vars(self):
                # Most `gen_value` methods return a value such as an integer,
                # string or dictionary, but OneTo{One,Many}Field.gen_value
                # returns an instance of the referenced class.
                if hasattr(field, 'default'):
                    value = field.default
                elif hasattr(field, 'choices'):
                    value = gen_choice(field.choices)
                elif isinstance(field, OneToOneField):
                    value = field.gen_value().create_json(auth=auth)['id']
                elif isinstance(field, OneToManyField):
                    value = [field.gen_value().create_json(auth=auth)['id']]
                else:
                    value = field.gen_value()
                setattr(self, field_name, value)

    def create_payload(self):
        """Create a payload that can be POSTed to the server.

        Make a copy of the instance attributes on ``self``. This payload will
        be POSTed to the server. Then change the payload's keys. (The payload
        is a dict.) Rename keys using ``self.Meta.api_names`` if it is present
        and append "_id" and "_ids" as appropriate.

        :return: A copy of the instance attributes on ``self``, with key names
            adjusted as appropriate.
        :rtype: dict

        """
        data = vars(self).copy()
        api_names = getattr(self.Meta, 'api_names', {})
        for field_name, field in type(self).get_fields().items():
            if field_name in data:
                if field_name in api_names:
                    # e.g. rename filter_type to type for ContentViewFilter
                    data[api_names[field_name]] = data.pop(field_name)
                if isinstance(field, OneToOneField):
                    data[field_name + '_id'] = data.pop(field_name)
                elif isinstance(field, OneToManyField):
                    data[field_name + '_ids'] = data.pop(field_name)
        return data

    def create_raw(self, auth=None, create_missing=True):
        """Create an entity.

        Generate values for required, unset fields by calling
        :meth:`create_missing`. Only do this if ``create_missing`` is true.
        Then make an HTTP POST call to ``self.path('base')``. Return the
        response received from the server.

        :param tuple auth: A ``(username, password)`` pair to use when
            communicating with the API. If ``None``, the credentials returned
            by :func:`robottelo.common.helpers.get_server_credentials` are
            used.
        :param bool create_missing: Should :meth:`create_missing` be called? In
            other words, should values be generated for required, empty fields?
        :return: A ``requests.response`` object.

        """
        if auth is None:
            auth = helpers.get_server_credentials()
        if create_missing:
            self.create_missing(auth)
        return client.post(
            self.path('base'),
            self.create_payload(),
            auth=auth,
            verify=False,
        )

    def create_json(self, auth=None, create_missing=True):
        """Create an entity.

        Call :meth:`create_raw`. Check the response status code, decode JSON
        and return the decoded JSON as a dict.

        :param tuple auth: Same as :meth:`create_raw`.
        :return: The server's response, with all JSON decoded.
        :rtype: dict
        :raises: ``requests.exceptions.HTTPError`` if the response has an HTTP
            4XX or 5XX status code.
        :raises: ``ValueError`` If the response JSON can not be decoded.

        """
        response = self.create_raw(auth, create_missing)
        response.raise_for_status()
        return response.json()

    def create(self, auth=None, create_missing=True):
        """Call :meth:`create_json`.

        This method exists for compatibility. It should be rewritten to match
        to act like :meth:`EntityReadMixin.read` after existing code is changed
        to use :meth:`create_json`.

        """
        return self.create_json(auth, create_missing)
