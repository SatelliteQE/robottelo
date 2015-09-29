# pylint: disable=too-many-public-methods
"""Data-driven unit tests for multiple paths."""
import httplib
import logging

from nailgun import client, entities, entity_fields
from requests.exceptions import HTTPError
from robottelo.config import conf
from robottelo.decorators import bz_bug_is_open, run_only_on, skip_if_bug_open
from robottelo.helpers import get_nailgun_config, get_server_credentials
from robottelo.test import APITestCase

logger = logging.getLogger(__name__)  # pylint:disable=invalid-name

BZ_1118015_ENTITIES = (
    entities.ActivationKey, entities.Architecture, entities.ConfigTemplate,
    entities.ContentView, entities.DockerComputeResource, entities.Environment,
    entities.GPGKey, entities.Host, entities.HostCollection,
    entities.HostGroup, entities.LibvirtComputeResource,
    entities.LifecycleEnvironment, entities.OperatingSystem, entities.Product,
    entities.Repository, entities.Role, entities.Subnet, entities.System,
    entities.User,
)
BZ_1154156_ENTITIES = (entities.ConfigTemplate, entities.Host, entities.User)
BZ_1187366_ENTITIES = (entities.LifecycleEnvironment, entities.Organization)


def valid_entities():
    """Returns a tuple of all valid entities."""
    return(
        entities.ActivationKey,
        entities.Architecture,
        entities.AuthSourceLDAP,
        entities.ComputeProfile,
        entities.ConfigTemplate,
        entities.ContentView,
        entities.DiscoveryRule,
        entities.DockerComputeResource,
        entities.Domain,
        entities.Environment,
        entities.GPGKey,
        entities.Host,
        entities.HostCollection,
        entities.LibvirtComputeResource,
        entities.HostGroup,
        entities.LifecycleEnvironment,
        entities.Media,
        entities.Model,
        entities.OperatingSystem,
        entities.Organization,
        entities.Product,
        entities.PuppetClass,
        entities.Repository,
        entities.Role,
        entities.Subnet,
        entities.System,
        entities.TemplateKind,
        entities.User,
        entities.UserGroup,
    )


def _get_readable_attributes(entity):
    """Return a dict of attributes matching what can be read from the server.

    When one reads an entity from the server, some attributes such as passwords
    are not returned. In addition, it is extremely hard to predict the exact
    format or naming of certain types of foreign key attributes. The remaining
    attributes, however, definitely should be present.

    Collect attributes from the ``entity`` object, drop attributes that the
    server doesn't hand back like passwords, drop foreign keys. What remains
    should match what the server will return.

    """
    attributes = entity.get_values()

    # Drop sensitive attributes.
    if isinstance(entity, entities.Host):
        del attributes['root_pass']
        del attributes['name']  # FIXME: "Foo" in, "foo.example.com" out.
    if isinstance(entity, entities.User):
        del attributes['password']
    if isinstance(entity, entities.System) and bz_bug_is_open(1202917):
        del attributes['facts']
        del attributes['type']

    # Drop foreign key attributes.
    for field_name in attributes.keys():
        if isinstance(
                entity.get_fields()[field_name],
                (entity_fields.OneToOneField, entity_fields.OneToManyField)
        ):
            del attributes[field_name]

    # The server deals with a field named "path", but we name the same field
    # path_ due to a naming conflict with a method by that name. Same w/search.
    if isinstance(entity, entities.Media):
        attributes['path'] = attributes.pop('path_')
    if isinstance(entity, entities.DiscoveryRule):
        attributes['search'] = attributes.pop('search_')

    return attributes


def skip_if_sam(self, entity):
    """Skip test if testing sam features and entity is unavailable in sam.

    Usage::

        def test_sample_test(self, entity):
            skip_if_sam(self, entity)
            # test code continues here

    The above code snippet skips the test when:

    * ``robottelo.properties`` is defined with ``main.project=sam``, and
    * the corresponding entity's definition in module ``nailgun.entities`` does
      not specify sam in server_modes. For example: ``server_modes = ('sat')``.

    :param entity: One of the entities defined in module ``nailgun.entities``.
    :returns: Either ``self.skipTest`` or ``None``.

    """
    robottelo_mode = conf.properties.get('main.project', '').lower()
    server_modes = [
        server_mode.lower()
        for server_mode
        in entity()._meta['server_modes']  # pylint:disable=protected-access
    ]

    if robottelo_mode == 'sam' and 'sam' not in server_modes:
        return self.skipTest(
            'Server runs in "{0}" mode and this entity is associated only to '
            '"{1}" mode(s).'.format(robottelo_mode, "".join(server_modes))
        )

    # else just return - do nothing!


class EntityTestCase(APITestCase):
    """Issue HTTP requests to various ``entity/`` paths."""

    def test_get_status_code(self):
        """@Test: GET an entity-dependent path.

        @Feature: Test multiple API paths

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        exclude_list = (
            entities.ActivationKey,  # need organization_id or environment_id
            entities.ContentView,  # need organization_id
            entities.GPGKey,  # need organization_id
            entities.HostCollection,  # need organization_id
            entities.LifecycleEnvironment,  # need organization_id
            entities.Product,  # need organization_id
            entities.Repository,  # need organization_id
            entities.System,  # need organization_id
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                logger.debug('test_get_status_code arg: %s', entity_cls)
                skip_if_sam(self, entity_cls)
                response = client.get(
                    entity_cls().path(),
                    auth=get_server_credentials(),
                    verify=False,
                )
                response.raise_for_status()
                self.assertEqual(httplib.OK, response.status_code)
                self.assertIn(
                    'application/json',
                    response.headers['content-type']
                )

    def test_get_unauthorized(self):
        """@Test: GET an entity-dependent path without credentials.

        @Feature: Test multiple API paths

        @Assert: HTTP 401 is returned

        """
        exclude_list = (
            entities.ActivationKey,  # need organization_id or environment_id
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                logger.debug('test_get_unauthorized arg: %s', entity_cls)
                skip_if_sam(self, entity_cls)
                response = client.get(
                    entity_cls().path(),
                    auth=(),
                    verify=False
                )
                self.assertEqual(httplib.UNAUTHORIZED, response.status_code)

    def test_post_status_code(self):
        """@Test: Issue a POST request and check the returned status code.

        @Feature: Test multiple API paths

        @Assert: HTTP 201 is returned with an ``application/json`` content-type

        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                logger.debug('test_post_status_code arg: %s', entity_cls)
                skip_if_sam(self, entity_cls)

                # Libvirt compute resources suffer from BZ 1118015. However,
                # partials cannot be compared for class identity and the class
                # hierarchy needs fixing (SatelliteQE/nailgun#42), so we just
                # comment it out above.
                if (entity_cls in BZ_1118015_ENTITIES and
                        bz_bug_is_open(1118015)):
                    self.skipTest('Bugzilla bug 1118015 is open.')

                response = entity_cls().create_raw()
                self.assertEqual(httplib.CREATED, response.status_code)
                self.assertIn(
                    'application/json',
                    response.headers['content-type']
                )

    @skip_if_bug_open('bugzilla', 1122257)
    def test_post_unauthorized(self):
        """@Test: POST to an entity-dependent path without credentials.

        @Feature: Test multiple API paths

        @Assert: HTTP 401 is returned

        """
        for entity_cls in valid_entities():
            with self.subTest(entity_cls):
                logger.debug('test_post_unauthorized arg: %s', entity_cls)
                skip_if_sam(self, entity_cls)
                server_cfg = get_nailgun_config()
                server_cfg.auth = ()
                return_code = entity_cls(server_cfg).create_raw(
                    create_missing=False
                ).status_code
                self.assertEqual(httplib.UNAUTHORIZED, return_code)


class EntityIdTestCase(APITestCase):
    """Issue HTTP requests to various ``entity/:id`` paths."""

    def test_get_status_code(self):
        """@Test: Create an entity and GET it.

        @Feature: Test multiple API paths

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                logger.debug('test_get_status_code arg: %s', entity_cls)
                skip_if_sam(self, entity_cls)
                try:
                    entity = entity_cls(id=entity_cls().create_json()['id'])
                except HTTPError as err:
                    self.fail(err)
                response = entity.read_raw()
                self.assertEqual(httplib.OK, response.status_code)
                self.assertIn(
                    'application/json',
                    response.headers['content-type']
                )

    def test_put_status_code(self):
        """@Test Issue a PUT request and check the returned status code.

        @Feature: Test multiple API paths

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                logger.debug('test_put_status_code arg: %s', entity_cls)
                skip_if_sam(self, entity_cls)
                if (entity_cls in BZ_1154156_ENTITIES and
                        bz_bug_is_open(1154156)):
                    self.skipTest("Bugzilla bug 1154156 is open.")

                # Create an entity
                entity_id = entity_cls().create_json()['id']

                # Update that entity.
                entity = entity_cls()
                entity.create_missing()
                response = client.put(
                    entity_cls(id=entity_id).path(),
                    # FIXME: use entity.update_payload()
                    entity.create_payload(),
                    auth=get_server_credentials(),
                    verify=False,
                )
                self.assertEqual(httplib.OK, response.status_code)
                self.assertIn(
                    'application/json',
                    response.headers['content-type']
                )

    def test_delete_status_code(self):
        """@Test Issue an HTTP DELETE request and check the returned status
        code.

        @Feature: Test multiple API paths

        @Assert: HTTP 200, 202 or 204 is returned with an ``application/json``
        content-type.

        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                logger.debug('test_delete_status_code arg: %s', entity_cls)
                skip_if_sam(self, entity_cls)
                if (entity_cls == entities.ConfigTemplate and
                        bz_bug_is_open(1096333)):
                    self.skipTest('Cannot delete config templates.')
                try:
                    entity = entity_cls(id=entity_cls().create_json()['id'])
                except HTTPError as err:
                    self.fail(err)
                response = entity.delete_raw()
                if (entity_cls in BZ_1187366_ENTITIES and
                        bz_bug_is_open(1187366)):
                    self.skipTest('BZ 1187366 is open.')
                self.assertIn(
                    response.status_code,
                    (httplib.NO_CONTENT, httplib.OK, httplib.ACCEPTED)
                )

                # According to RFC 2616, HTTP 204 responses "MUST NOT include a
                # message-body". If a message does not have a body, there is no
                # need to set the content-type of the message.
                if response.status_code is not httplib.NO_CONTENT:
                    self.assertIn(
                        'application/json',
                        response.headers['content-type']
                    )


class DoubleCheckTestCase(APITestCase):
    """Perform in-depth tests on URLs.

    Do not just assume that an HTTP response with a good status code indicates
    that an action succeeded. Instead, issue a follow-up request after each
    action to ensure that the intended action was accomplished.

    """
    longMessage = True

    def test_put_and_get(self):
        """@Test: Update an entity, then read it back.

        @Feature: Test multiple API paths

        @Assert: The entity is updated with the given attributes.

        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                logger.debug('test_put_and_get arg: %s', entity_cls)
                skip_if_sam(self, entity_cls)
                if (entity_cls in BZ_1154156_ENTITIES and
                        bz_bug_is_open(1154156)):
                    self.skipTest("Bugzilla bug 1154156 is open.")

                # Create an entity.
                entity_id = entity_cls().create_json()['id']

                # Update that entity. FIXME: This whole procedure is a hack.
                entity = entity_cls()
                # Generate randomized instance attributes
                entity.create_missing()
                response = client.put(
                    entity_cls(id=entity_id).path(),
                    entity.create_payload(),
                    auth=get_server_credentials(),
                    verify=False,
                )
                response.raise_for_status()

                # Compare `payload` against entity information returned by the
                # server.
                payload = _get_readable_attributes(entity)
                entity_attrs = entity_cls(id=entity_id).read_json()
                for key, value in payload.items():
                    self.assertIn(key, entity_attrs.keys())
                    self.assertEqual(value, entity_attrs[key], key)

    def test_post_and_get(self):
        """@Test: Create an entity, then read it back.

        @Feature: Test multiple API paths

        @Assert: The entity is created with the given attributes.

        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                logger.debug('test_post_and_get arg: %s', entity_cls)
                skip_if_sam(self, entity_cls)
                if (entity_cls in BZ_1154156_ENTITIES and
                        bz_bug_is_open(1154156)):
                    self.skipTest('Bugzilla bug 1154156 is open.')

                entity = entity_cls()
                entity_id = entity.create_json()['id']

                # Compare `payload` against entity information returned by the
                # server.
                payload = _get_readable_attributes(entity)
                entity_attrs = entity_cls(id=entity_id).read_json()
                for key, value in payload.items():
                    self.assertIn(key, entity_attrs.keys())
                    self.assertEqual(value, entity_attrs[key], key)

    def test_delete_and_get(self):
        """@Test: Issue an HTTP DELETE request and GET the deleted entity.

        @Feature: Test multiple API paths

        @Assert: An HTTP 404 is returned when fetching the missing entity.

        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                logger.debug('test_delete_and_get arg: %s', entity_cls)
                skip_if_sam(self, entity_cls)
                if (entity_cls is entities.ConfigTemplate and
                        bz_bug_is_open(1096333)):
                    self.skipTest('BZ 1096333: Cannot delete config templates')
                if (entity_cls in BZ_1187366_ENTITIES and
                        bz_bug_is_open(1187366)):
                    self.skipTest('BZ 1187366: Cannot delete orgs or envs.')
                if entity_cls == entities.System and bz_bug_is_open(1133071):
                    self.skipTest(
                        'BZ 1133071: Receive HTTP 400s instead of 404s.'
                    )

                # Create an entity, delete it and get it.
                try:
                    entity = entity_cls(id=entity_cls().create_json()['id'])
                except HTTPError as err:
                    self.fail(err)
                entity.delete()
                self.assertEqual(
                    httplib.NOT_FOUND,
                    entity.read_raw().status_code
                )


class EntityReadTestCase(APITestCase):
    """
    Check that classes inheriting from
    ``nailgun.entity_mixins.EntityReadMixin`` function correctly.
    """
    def test_entity_read(self):
        """@Test: Create an entity and get it using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        @Feature: Test multiple API paths

        @Assert: The just-read entity is an instance of the correct class.

        """
        exclude_list = (
            entities.Architecture,  # see test_architecture_read
            entities.OperatingSystemParameter,  # see test_osparameter_read
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                logger.debug('test_entity_read arg: %s', entity_cls)
                skip_if_sam(self, entity_cls)
                if entity_cls == entities.System and bz_bug_is_open(1223494):
                    self.skipTest('Cannot read all system attributes.')
                entity_id = entity_cls().create_json()['id']
                self.assertIsInstance(
                    entity_cls(id=entity_id).read(),
                    entity_cls
                )

    def test_architecture_read(self):
        """@Test: Create an arch that points to an OS, and read the arch.

        @Feature: Test multiple API paths

        @Assert: The call to ``Architecture.read`` succeeds, and the response
        contains the correct operating system ID.

        """
        os_id = entities.OperatingSystem().create_json()['id']
        arch_id = entities.Architecture(
            operatingsystem=[os_id]
        ).create_json()['id']
        architecture = entities.Architecture(id=arch_id).read()
        self.assertEqual(len(architecture.operatingsystem), 1)
        self.assertEqual(architecture.operatingsystem[0].id, os_id)

    def test_syncplan_read(self):
        """@Test: Create a SyncPlan and read it back using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        @Feature: Test multiple API paths.

        @Assert: The just-read entity is an instance of the correct class.

        """
        org_id = entities.Organization().create_json()['id']
        syncplan_id = entities.SyncPlan(
            organization=org_id
        ).create_json()['id']
        self.assertIsInstance(
            entities.SyncPlan(organization=org_id, id=syncplan_id).read(),
            entities.SyncPlan
        )

    @run_only_on('sat')
    def test_osparameter_read(self):
        """@Test: Create an OperatingSystemParameter and get it using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        @Feature: Test multiple API paths

        @Assert: The just-read entity is an instance of the correct class.

        """
        os_id = entities.OperatingSystem().create_json()['id']
        osp_id = entities.OperatingSystemParameter(
            operatingsystem=os_id
        ).create_json()['id']
        self.assertIsInstance(
            entities.OperatingSystemParameter(
                id=osp_id,
                operatingsystem=os_id,
            ).read(),
            entities.OperatingSystemParameter
        )

    @run_only_on('sat')
    def test_permission_read(self):
        """@Test: Create an Permission entity and get it using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        @Feature: Test multiple API paths

        @Assert: The just-read entity is an instance of the correct class and
        name and resource_type fields are populated

        """
        perm = entities.Permission().search(query={'per_page': 1})[0]
        self.assertGreater(len(perm.name), 0)
        self.assertGreater(len(perm.resource_type), 0)

    def test_media_read(self):
        """@Test: Create a media pointing at an OS and read the media.

        @Feature: Test multiple API paths

        @Assert: The media points at the correct operating system.

        """
        os_id = entities.OperatingSystem().create_json()['id']
        media_id = entities.Media(operatingsystem=[os_id]).create_json()['id']
        media = entities.Media(id=media_id).read()
        self.assertEqual(len(media.operatingsystem), 1)
        self.assertEqual(media.operatingsystem[0].id, os_id)
