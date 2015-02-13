"""Data-driven unit tests for multiple paths."""
from ddt import data, ddt
from robottelo.api import client
from robottelo.api.utils import status_code_error
from robottelo.common.decorators import bz_bug_is_open, skip_if_bug_open
from robottelo.common.helpers import get_server_credentials
from robottelo import entities, factory
from unittest import TestCase
import httplib
import logging
# (too many public methods) pylint: disable=R0904


logger = logging.getLogger(__name__)  # pylint:disable=C0103


BZ_1118015_ENTITIES = (
    entities.ActivationKey, entities.Architecture, entities.ConfigTemplate,
    entities.ContentView, entities.Environment, entities.GPGKey,
    entities.HostCollection, entities.LifecycleEnvironment,
    entities.OperatingSystem, entities.Product, entities.Repository,
    entities.Role, entities.System, entities.User,
)
BZ_1151240_ENTITIES = (
    entities.ActivationKey, entities.ContentView, entities.GPGKey,
    entities.LifecycleEnvironment, entities.Product, entities.Repository
)


@ddt
class EntityTestCase(TestCase):
    """Issue HTTP requests to various ``entity/`` paths."""
    @data(
        # entities.ActivationKey,  # need organization_id or environment_id
        entities.Architecture,
        entities.ComputeProfile,
        entities.ConfigTemplate,
        # entities.ContentView,  # need organization_id
        entities.Domain,
        entities.Environment,
        # entities.GPGKey,  # need organization_id
        entities.Host,
        # entities.HostCollection,  # need organization_id
        # entities.LifecycleEnvironment,  # need organization_id
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        # entities.Product,  # need organization_id
        # entities.Repository,  # need organization_id
        entities.Role,
        # entities.System,  # need organization_id
        entities.TemplateKind,
        entities.User,
    )
    def test_get_status_code(self, entity):
        """@Test GET an entity-dependent path.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        response = entity().read_raw()
        status_code = httplib.OK
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(entity().path(), status_code, response),
        )
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        # entities.ActivationKey,  # need organization id or environment id
        entities.Architecture,
        entities.ComputeProfile,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.System,
        entities.TemplateKind,
        entities.User,
    )
    def test_get_unauthorized(self, entity):
        """@Test: GET an entity-dependent path without credentials.

        @Assert: HTTP 401 is returned

        """
        response = entity().read_raw(auth=())
        status_code = httplib.UNAUTHORIZED
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(entity().path(), status_code, response),
        )

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ComputeProfile,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        # entities.Host,  # Host().create() does not work
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.System,
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_post_status_code(self, entity):
        """@Test: Issue a POST request and check the returned status code.

        @Assert: HTTP 201 is returned with an ``application/json`` content-type

        """
        if entity in BZ_1118015_ENTITIES and bz_bug_is_open(1118015):
            self.skipTest('Bugzilla bug 1118015 is open.')
        path = entity().path()
        response = client.post(
            path,
            entity().build(),
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.CREATED
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ComputeProfile,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        entities.System,
        entities.TemplateKind,
        entities.User,
    )
    @skip_if_bug_open('bugzilla', 1122257)
    def test_post_unauthorized(self, entity):
        """@Test: POST to an entity-dependent path without credentials.

        @Assert: HTTP 401 is returned

        """
        path = entity().path()
        response = client.post(path, verify=False)
        status_code = httplib.UNAUTHORIZED
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )


@ddt
class EntityIdTestCase(TestCase):
    """Issue HTTP requests to various ``entity/:id`` paths."""
    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ComputeProfile,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        # entities.Host,  # Host().create() does not work
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_get_status_code(self, entity):
        """@Test: Create an entity and GET it.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        try:
            entity_n = entity(id=entity().create()['id'])
        except factory.FactoryError as err:
            self.fail(err)
        response = entity_n.read_raw()
        status_code = httplib.OK
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(entity_n.path(), status_code, response),
        )
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ComputeProfile,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        # entities.Host,  # Host().create() does not work
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_put_status_code(self, entity):
        """@Test Issue a PUT request and check the returned status code.

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        path = entity(id=entity().create()['id']).path()
        response = client.put(
            path,
            entity().attributes(),
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = httplib.OK
        self.assertEqual(
            status_code,
            response.status_code,
            status_code_error(path, status_code, response),
        )
        self.assertIn('application/json', response.headers['content-type'])

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ComputeProfile,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        # entities.Host,  # Host().create() does not work
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_delete_status_code(self, entity):
        """@Test Issue an HTTP DELETE request and check the returned status
        code.

        @Assert: HTTP 200, 202 or 204 is returned with an ``application/json``
        content-type.

        """
        if entity is entities.ConfigTemplate and bz_bug_is_open(1096333):
            self.skipTest('Cannot delete config templates.')
        try:
            attrs = entity().create()
        except factory.FactoryError as err:
            self.fail(err)
        path = entity(id=attrs['id']).path()
        response = client.delete(
            path,
            auth=get_server_credentials(),
            verify=False,
        )
        status_code = (httplib.NO_CONTENT, httplib.OK, httplib.ACCEPTED)
        self.assertIn(
            response.status_code,
            status_code,
            status_code_error(path, status_code, response),
        )

        # According to RFC 2616, HTTP 204 responses "MUST NOT include a
        # message-body". If a message does not have a body, there is no need to
        # set the content-type of the message.
        if response.status_code is not httplib.NO_CONTENT:
            self.assertIn('application/json', response.headers['content-type'])


@ddt
class DoubleCheckTestCase(TestCase):
    """Perform in-depth tests on URLs.

    Do not just assume that an HTTP response with a good status code indicates
    that an action succeeded. Instead, issue a follow-up request after each
    action to ensure that the intended action was accomplished.

    """
    longMessage = True

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ComputeProfile,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        # entities.Host,  # Host().create() does not work
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        # entities.User,  # password not in returned attrs
    )
    def test_put_and_get(self, entity):
        """@Test: Issue a PUT request and GET the updated entity.

        @Assert: The updated entity has the correct attributes.

        """
        entity_n = entity(id=entity().create()['id'])
        logger.info('test_put_and_get path: {0}'.format(entity_n.path()))

        # Generate some attributes and use them to update an entity.
        gen_attrs = entity().attributes()
        response = client.put(
            entity_n.path(),
            gen_attrs,
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()

        # Get the just-updated entity and examine its attributes.
        real_attrs = entity_n.read_json()
        for key, value in gen_attrs.items():
            self.assertIn(key, real_attrs.keys())
            self.assertEqual(value, real_attrs[key], key)

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ComputeProfile,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        # entities.Host,  # Host().create() does not work
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        # entities.User,  # password not in returned attrs
    )
    def test_post_and_get(self, entity):
        """@Test Issue a POST request and GET the created entity.

        @Assert: The created entity has the correct attributes.

        """
        if entity in BZ_1151240_ENTITIES:
            self.skipTest("Bugzilla bug 1151240 affects the 6.0.x branch.")
        # Generate some attributes and use them to create an entity.
        gen_attrs = entity().build()
        response = client.post(
            entity().path(),
            gen_attrs,
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()

        # Get the just-created entity and examine its attributes.
        entity_n = entity(id=response.json()['id'])
        logger.info('test_post_and_get path: {0}'.format(entity_n.path()))
        real_attrs = entity_n.read_json()
        for key, value in gen_attrs.items():
            self.assertIn(key, real_attrs.keys())
            self.assertEqual(value, real_attrs[key], key)

    @data(
        entities.ActivationKey,
        entities.Architecture,
        entities.ComputeProfile,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        # entities.Host,  # Host().create() does not work
        entities.HostCollection,
        entities.LifecycleEnvironment,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.Repository,
        entities.Role,
        # entities.System,  # See test_activationkey_v2.py
        # entities.TemplateKind,  # see comments in class definition
        entities.User,
    )
    def test_delete_and_get(self, entity):
        """@Test: Issue an HTTP DELETE request and GET the deleted entity.

        @Assert: An HTTP 404 is returned when fetching the missing entity.

        """
        if entity is entities.ConfigTemplate and bz_bug_is_open(1096333):
            self.skipTest('Cannot delete config templates.')

        # Create an entity, then delete it.
        try:
            entity_n = entity(id=entity().create()['id'])
        except factory.FactoryError as err:
            self.fail(err)
        logger.info('test_delete_and_get path: {0}'.format(entity_n.path()))
        entity_n.delete()

        # An HTTP 404 response code should always be returned, but this bug is
        # unlikely to be fixed in a z-stream release due to how minor it is.
        status_codes = [httplib.NOT_FOUND]
        if entity == entities.Repository:
            status_codes.append(httplib.BAD_REQUEST)

        # Get the now non-existent entity.
        response = entity_n.read_raw()
        self.assertIn(response.status_code, status_codes, response.text)


@ddt
class EntityReadTestCase(TestCase):
    """
    Check that classes inheriting from :class:`robottelo.orm.EntityReadMixin`
    function correctly.
    """
    # Most entities are commented-out because they do not inherit from
    # EntityReadMixin, due to issues with data returned from the API.
    @data(
        # entities.ActivationKey,
        # entities.Architecture,
        entities.ComputeProfile,
        # entities.ConfigTemplate,
        # entities.ContentView,
        # entities.Domain,
        entities.Environment,
        # entities.GPGKey,
        # entities.Host,  # Host().create() does not work
        entities.HostCollection,
        # entities.LifecycleEnvironment,
        entities.Model,
        entities.OperatingSystem,
        # entities.OperatingSystemParameter,  # see test_osparameter_read
        entities.Organization,
        # entities.Product,
        entities.Repository,
        entities.Role,
        # entities.System,
        # entities.TemplateKind,  # see comments in class definition
        # entities.User,
    )
    def test_entity_read(self, entity):
        """@Test: Create an entity and get it using
        :meth:`robottelo.orm.EntityReadMixin.read`.

        @Assert: The just-read entity is an instance of the correct class.

        """
        attrs = entity().create()
        read_entity = entity(id=attrs['id']).read()
        self.assertIsInstance(read_entity, entity)

    def test_osparameter_read(self):
        """@Test: Create an OperatingSystemParameter and get it using
        :meth:`robottelo.orm.EntityReadMixin.read`.

        @Assert: The just-read entity is an instance of the correct class.

        """
        os_attrs = entities.OperatingSystem().create()
        osp_attrs = entities.OperatingSystemParameter(os_attrs['id']).create()
        self.assertIsInstance(
            entities.OperatingSystemParameter(
                os_attrs['id'],
                id=osp_attrs['id'],
            ).read(),
            entities.OperatingSystemParameter
        )
