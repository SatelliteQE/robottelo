"""Data-driven unit tests for multiple paths.

:Requirement: Multiple Paths

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import logging

from nailgun import client, entities, entity_fields
from requests.exceptions import HTTPError
from robottelo.config import settings
from robottelo.decorators import (
    tier1,
    tier3,
)
from robottelo.helpers import get_nailgun_config
from robottelo.test import APITestCase
from six.moves import http_client

logger = logging.getLogger(__name__)

BZ_1118015_ENTITIES = (
    entities.ActivationKey, entities.Architecture, entities.ConfigTemplate,
    entities.ContentView, entities.DockerComputeResource, entities.Environment,
    entities.GPGKey, entities.Host, entities.HostCollection,
    entities.HostGroup, entities.LibvirtComputeResource,
    entities.LifecycleEnvironment, entities.OperatingSystem,
    entities.Organization, entities.Product, entities.Repository,
    entities.Role, entities.Subnet, entities.User,
)


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

    # Drop foreign key attributes.
    for field_name in list(attributes.keys()):
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


class EntityTestCase(APITestCase):
    """Issue HTTP requests to various ``entity/`` paths."""

    @staticmethod
    def get_entities_for_unauthorized(all_entities, exclude_entities):
        """Limit the number of entities that have to be tested for negative
        unauthorized tests.
        """
        # FIXME: this must be replaced by a setup function that disable
        # "Brute-force attack prevention" for negative tests when disabling
        # feature is available downstream
        max_entities = 10
        test_entities = list(set(all_entities) - set(exclude_entities))
        if len(test_entities) > max_entities:
            test_entities = test_entities[:max_entities]
        return test_entities

    @tier3
    def test_positive_get_status_code(self):
        """GET an entity-dependent path.

        :id: 89e4fafe-7780-4be4-acc1-90f7c02a8530

        :expectedresults: HTTP 200 is returned with an ``application/json``
            content-type

        :CaseImportance: Critical
        """
        exclude_list = (
            entities.ActivationKey,  # need organization_id or environment_id
            entities.ContentView,  # need organization_id
            entities.GPGKey,  # need organization_id
            entities.HostCollection,  # need organization_id
            entities.LifecycleEnvironment,  # need organization_id
            entities.Product,  # need organization_id
            entities.Repository,  # need organization_id
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                self.logger.info('test_get_status_code arg: %s', entity_cls)
                response = client.get(
                    entity_cls().path(),
                    auth=settings.server.get_credentials(),
                    verify=False,
                )
                response.raise_for_status()
                self.assertEqual(http_client.OK, response.status_code)
                self.assertIn(
                    'application/json',
                    response.headers['content-type']
                )

    @tier1
    def test_negative_get_unauthorized(self):
        """GET an entity-dependent path without credentials.

        :id: 49127c71-55a2-42d1-b418-59229e9bad00

        :expectedresults: HTTP 401 is returned

        :CaseImportance: Critical
        """
        exclude_list = (
            entities.ActivationKey,  # need organization_id or environment_id
        )
        test_entities = self.get_entities_for_unauthorized(
            valid_entities(), exclude_list)
        for entity_cls in test_entities:
            with self.subTest(entity_cls):
                self.logger.info('test_get_unauthorized arg: %s', entity_cls)
                response = client.get(
                    entity_cls().path(),
                    auth=(),
                    verify=False
                )
                self.assertEqual(
                    http_client.UNAUTHORIZED, response.status_code)

    @tier3
    def test_positive_post_status_code(self):
        """Issue a POST request and check the returned status code.

        :id: 40247cdd-ad72-4b7b-97c6-583addb1b25a

        :expectedresults: HTTP 201 is returned with an ``application/json``
            content-type

        :CaseImportance: Critical

        :BZ: 1118015
        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                self.logger.info('test_post_status_code arg: %s', entity_cls)

                # Libvirt compute resources suffer from BZ 1118015. However,
                # partials cannot be compared for class identity and the class
                # hierarchy needs fixing (SatelliteQE/nailgun#42), so we just
                # comment it out above.
                if entity_cls in BZ_1118015_ENTITIES:
                    continue  # pytest can't skip inside a subTest.

                response = entity_cls().create_raw()
                self.assertEqual(http_client.CREATED, response.status_code)
                self.assertIn(
                    'application/json',
                    response.headers['content-type']
                )

    @tier1
    def test_negative_post_unauthorized(self):
        """POST to an entity-dependent path without credentials.

        :id: 2ec82336-5bcc-451a-90ed-9abcecc5a0a8

        :expectedresults: HTTP 401 is returned

        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        test_entities = self.get_entities_for_unauthorized(
            valid_entities(), exclude_list)
        for entity_cls in test_entities:
            with self.subTest(entity_cls):
                self.logger.info('test_post_unauthorized arg: %s', entity_cls)
                server_cfg = get_nailgun_config()
                server_cfg.auth = ()
                return_code = entity_cls(server_cfg).create_raw(
                    create_missing=False
                ).status_code
                self.assertEqual(http_client.UNAUTHORIZED, return_code)


class EntityIdTestCase(APITestCase):
    """Issue HTTP requests to various ``entity/:id`` paths."""

    @tier1
    def test_positive_get_status_code(self):
        """Create an entity and GET it.

        :id: 4fb6cca6-c63f-4d4f-811e-53bf4e6b9752

        :expectedresults: HTTP 200 is returned with an ``application/json``
            content-type

        :CaseImportance: Critical
        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                self.logger.info('test_get_status_code arg: %s', entity_cls)
                try:
                    entity = entity_cls(id=entity_cls().create_json()['id'])
                except HTTPError as err:
                    self.fail(err)
                response = entity.read_raw()
                self.assertEqual(http_client.OK, response.status_code)
                self.assertIn(
                    'application/json',
                    response.headers['content-type']
                )

    @tier1
    def test_positive_put_status_code(self):
        """Issue a PUT request and check the returned status code.

        :id: 1a2186b1-0709-4a73-8199-71114e10afce

        :expectedresults: HTTP 200 is returned with an ``application/json``
            content-type

        :CaseImportance: Critical

        :BZ: 1378009
        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                self.logger.info('test_put_status_code arg: %s', entity_cls)

                # Create an entity
                entity_id = entity_cls().create_json()['id']

                # Update that entity.
                entity = entity_cls()
                entity.create_missing()
                response = client.put(
                    entity_cls(id=entity_id).path(),
                    # FIXME: use entity.update_payload()
                    entity.create_payload(),
                    auth=settings.server.get_credentials(),
                    verify=False,
                )
                self.assertEqual(http_client.OK, response.status_code)
                self.assertIn(
                    'application/json',
                    response.headers['content-type']
                )

    @tier1
    def test_positive_delete_status_code(self):
        """Issue an HTTP DELETE request and check the returned status
        code.

        :id: bacf4bf2-eb2b-4201-a21c-8d15f5b06e7a

        :expectedresults: HTTP 200, 202 or 204 is returned with an
            ``application/json`` content-type.

        :CaseImportance: Critical
        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                self.logger.info('test_delete_status_code arg: %s', entity_cls)
                try:
                    entity = entity_cls(id=entity_cls().create_json()['id'])
                except HTTPError as err:
                    self.fail(err)
                response = entity.delete_raw()
                self.assertIn(
                    response.status_code,
                    (
                        http_client.NO_CONTENT,
                        http_client.OK,
                        http_client.ACCEPTED,
                    )
                )

                # According to RFC 2616, HTTP 204 responses "MUST NOT include a
                # message-body". If a message does not have a body, there is no
                # need to set the content-type of the message.
                if response.status_code is not http_client.NO_CONTENT:
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

    @tier1
    def test_positive_put_and_get_requests(self):
        """Update an entity, then read it back.

        :id: f5d3039f-5468-4dd2-8ac9-6e948ef39866

        :expectedresults: The entity is updated with the given attributes.

        :CaseImportance: Medium

        :BZ: 1378009
        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                self.logger.info('test_put_and_get arg: %s', entity_cls)

                # Create an entity.
                entity_id = entity_cls().create_json()['id']

                # Update that entity. FIXME: This whole procedure is a hack.
                entity = entity_cls()
                # Generate randomized instance attributes
                entity.create_missing()
                response = client.put(
                    entity_cls(id=entity_id).path(),
                    entity.create_payload(),
                    auth=settings.server.get_credentials(),
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

    @tier1
    def test_positive_post_and_get_requests(self):
        """Create an entity, then read it back.

        :id: c658095b-2bf9-4c3e-8ddf-c1792e743a10

        :expectedresults: The entity is created with the given attributes.

        :CaseImportance: Medium
        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                self.logger.info('test_post_and_get arg: %s', entity_cls)

                entity = entity_cls()
                entity_id = entity.create_json()['id']

                # Compare `payload` against entity information returned by the
                # server.
                payload = _get_readable_attributes(entity)
                entity_attrs = entity_cls(id=entity_id).read_json()
                for key, value in payload.items():
                    self.assertIn(key, entity_attrs.keys())
                    self.assertEqual(value, entity_attrs[key], key)

    @tier1
    def test_positive_delete_and_get_requests(self):
        """Issue an HTTP DELETE request and GET the deleted entity.

        :id: 04a37ba7-c553-40e1-bc4c-ec2ebf567647

        :expectedresults: An HTTP 404 is returned when fetching the missing
            entity.

        :CaseImportance: Critical
        """
        exclude_list = (
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                self.logger.info('test_delete_and_get arg: %s', entity_cls)

                # Create an entity, delete it and get it.
                try:
                    entity = entity_cls(id=entity_cls().create_json()['id'])
                except HTTPError as err:
                    self.fail(err)
                entity.delete()
                self.assertEqual(
                    http_client.NOT_FOUND,
                    entity.read_raw().status_code
                )


class EntityReadTestCase(APITestCase):
    """Check whether classes inherited from
    ``nailgun.entity_mixins.EntityReadMixin`` are working properly.
    """

    @tier1
    def test_positive_entity_read(self):
        """Create an entity and get it using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        :id: 78bddedd-bbcf-4e26-a9f7-746874f58529

        :expectedresults: The just-read entity is an instance of the correct
            class.

        :CaseImportance: Critical
        """
        exclude_list = (
            entities.Architecture,  # see test_architecture_read
            entities.OperatingSystemParameter,  # see test_osparameter_read
            entities.TemplateKind,  # see comments in class definition
        )
        for entity_cls in set(valid_entities()) - set(exclude_list):
            with self.subTest(entity_cls):
                self.logger.info('test_entity_read arg: %s', entity_cls)
                entity_id = entity_cls().create_json()['id']
                self.assertIsInstance(
                    entity_cls(id=entity_id).read(),
                    entity_cls
                )

    @tier1
    def test_positive_architecture_read(self):
        """Create an arch that points to an OS, and read the arch.

        :id: e4c7babe-11d8-4f85-8382-5267a49046e9

        :expectedresults: The call to ``Architecture.read`` succeeds, and the
            response contains the correct operating system ID.

        :CaseImportance: Critical
        """
        os_id = entities.OperatingSystem().create_json()['id']
        arch_id = entities.Architecture(
            operatingsystem=[os_id]
        ).create_json()['id']
        architecture = entities.Architecture(id=arch_id).read()
        self.assertEqual(len(architecture.operatingsystem), 1)
        self.assertEqual(architecture.operatingsystem[0].id, os_id)

    @tier1
    def test_positive_syncplan_read(self):
        """Create a SyncPlan and read it back using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        :id: 2a5f53c7-262a-44a6-b7bf-d57fbaef3dc7

        :expectedresults: The just-read entity is an instance of the correct
            class.

        :CaseImportance: Critical
        """
        org_id = entities.Organization().create_json()['id']
        syncplan_id = entities.SyncPlan(
            organization=org_id
        ).create_json()['id']
        self.assertIsInstance(
            entities.SyncPlan(organization=org_id, id=syncplan_id).read(),
            entities.SyncPlan
        )

    @tier1
    def test_positive_osparameter_read(self):
        """Create an OperatingSystemParameter and get it using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        :id: 1de63937-5ca1-4101-b4ee-4b398c66b630

        :expectedresults: The just-read entity is an instance of the correct
            class.

        :CaseImportance: Critical
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

    @tier1
    def test_positive_permission_read(self):
        """Create an Permission entity and get it using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        :id: 5631a1eb-33ff-4abe-bf01-6c8d98c47a96

        :expectedresults: The just-read entity is an instance of the correct
            class and name and resource_type fields are populated

        :CaseImportance: Critical
        """
        perm = entities.Permission().search(query={'per_page': 1})[0]
        self.assertGreater(len(perm.name), 0)
        self.assertGreater(len(perm.resource_type), 0)

    @tier1
    def test_positive_media_read(self):
        """Create a media pointing at an OS and read the media.

        :id: 67b656fe-9302-457a-b544-3addb11c85e0

        :expectedresults: The media points at the correct operating system.

        :CaseImportance: Critical
        """
        os_id = entities.OperatingSystem().create_json()['id']
        media_id = entities.Media(operatingsystem=[os_id]).create_json()['id']
        media = entities.Media(id=media_id).read()
        self.assertEqual(len(media.operatingsystem), 1)
        self.assertEqual(media.operatingsystem[0].id, os_id)
