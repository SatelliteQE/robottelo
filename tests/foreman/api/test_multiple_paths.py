"""Data-driven unit tests for multiple paths.

:Requirement: Multiple Paths

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:Assignee: lhellebr

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import http

import pytest
from nailgun import client
from nailgun import entities
from nailgun import entity_fields

from robottelo.config import settings
from robottelo.datafactory import parametrized
from robottelo.helpers import get_nailgun_config
from robottelo.logging import logger


VALID_ENTITIES = {
    entities.ActivationKey,
    entities.Architecture,
    entities.AuthSourceLDAP,
    entities.ComputeProfile,
    entities.ProvisioningTemplate,
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
}
STATUS_CODE_ENTITIES = {
    entities.ActivationKey,  # need organization_id or environment_id
    entities.ContentView,  # need organization_id
    entities.GPGKey,  # need organization_id
    entities.HostCollection,  # need organization_id
    entities.LifecycleEnvironment,  # need organization_id
    entities.Product,  # need organization_id
    entities.Repository,  # need organization_id
}


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
            (entity_fields.OneToOneField, entity_fields.OneToManyField),
        ):
            del attributes[field_name]

    # The server deals with a field named "path", but we name the same field
    # path_ due to a naming conflict with a method by that name. Same w/search.
    if isinstance(entity, entities.Media):
        attributes['path'] = attributes.pop('path_')
    if isinstance(entity, entities.DiscoveryRule):
        attributes['search'] = attributes.pop('search_')

    return attributes


def get_entities_for_unauthorized(all_entities, exclude_entities, max_num=10):
    """Limit the number of entities that have to be tested for negative
    unauthorized tests.
    """
    # FIXME: this must be replaced by a setup function that disable
    # 'Brute-force attack prevention' for negative tests when disabling
    # feature is available downstream
    return list(all_entities - exclude_entities)[:max_num]


class TestEntity:
    """Issue HTTP requests to various ``entity/`` paths."""

    @pytest.mark.tier3
    @pytest.mark.parametrize(
        'entity_cls',
        **parametrized(VALID_ENTITIES - STATUS_CODE_ENTITIES),
    )
    def test_positive_get_status_code(self, entity_cls):
        """GET an entity-dependent path.

        :id: 89e4fafe-7780-4be4-acc1-90f7c02a8530

        :parametrized: yes

        :expectedresults: HTTP 200 is returned with an ``application/json``
            content-type

        :CaseImportance: Critical
        """
        logger.info('test_get_status_code arg: %s', entity_cls)
        response = client.get(
            entity_cls().path(), auth=settings.server.get_credentials(), verify=False
        )
        response.raise_for_status()
        assert http.client.OK == response.status_code
        assert 'application/json' in response.headers['content-type']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls',
        **parametrized(get_entities_for_unauthorized(VALID_ENTITIES, {entities.ActivationKey})),
    )
    def test_negative_get_unauthorized(self, entity_cls):
        """GET an entity-dependent path without credentials.

        :id: 49127c71-55a2-42d1-b418-59229e9bad00

        :parametrized: yes

        :expectedresults: HTTP 401 is returned

        :CaseImportance: Critical
        """
        logger.info('test_get_unauthorized arg: %s', entity_cls)
        response = client.get(entity_cls().path(), auth=(), verify=False)
        assert http.client.UNAUTHORIZED == response.status_code

    @pytest.mark.tier3
    @pytest.mark.parametrize(
        'entity_cls',
        **parametrized(get_entities_for_unauthorized(VALID_ENTITIES, {entities.TemplateKind})),
    )
    def test_positive_post_status_code(self, entity_cls):
        """Issue a POST request and check the returned status code.

        :id: 40247cdd-ad72-4b7b-97c6-583addb1b25a

        :parametrized: yes

        :expectedresults: HTTP 201 is returned with an ``application/json``
            content-type

        :CaseImportance: Critical

        :BZ: 1118015
        """
        response = entity_cls().create_raw()
        assert http.client.CREATED == response.status_code
        assert 'application/json' in response.headers['content-type']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls',
        **parametrized(get_entities_for_unauthorized(VALID_ENTITIES, {entities.TemplateKind})),
    )
    def test_negative_post_unauthorized(self, entity_cls):
        """POST to an entity-dependent path without credentials.

        :id: 2ec82336-5bcc-451a-90ed-9abcecc5a0a8

        :parametrized: yes

        :expectedresults: HTTP 401 is returned

        :BZ: 1122257

        """
        server_cfg = get_nailgun_config()
        server_cfg.auth = ()
        return_code = entity_cls(server_cfg).create_raw(create_missing=False).status_code
        assert http.client.UNAUTHORIZED == return_code


class TestEntityId:
    """Issue HTTP requests to various ``entity/:id`` paths."""

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls', **parametrized(VALID_ENTITIES - {entities.TemplateKind})
    )
    def test_positive_get_status_code(self, entity_cls):
        """Create an entity and GET it.

        :id: 4fb6cca6-c63f-4d4f-811e-53bf4e6b9752

        :parametrized: yes

        :expectedresults: HTTP 200 is returned with an ``application/json``
            content-type

        :CaseImportance: Critical
        """
        entity = entity_cls(id=entity_cls().create_json()['id'])
        response = entity.read_raw()
        assert http.client.OK == response.status_code
        assert 'application/json' in response.headers['content-type']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls', **parametrized(VALID_ENTITIES - {entities.TemplateKind})
    )
    def test_positive_put_status_code(self, entity_cls):
        """Issue a PUT request and check the returned status code.

        :id: 1a2186b1-0709-4a73-8199-71114e10afce

        :parametrized: yes

        :expectedresults: HTTP 200 is returned with an ``application/json``
            content-type

        :CaseImportance: Critical

        :BZ: 1378009
        """
        # Create an entity
        entity_id = entity_cls().create_json()['id']

        # Update that entity.
        entity = entity_cls()
        entity.create_missing()
        response = client.put(
            entity_cls(id=entity_id).path(),
            entity.update_payload(),
            auth=settings.server.get_credentials(),
            verify=False,
        )
        assert http.client.OK == response.status_code
        assert 'application/json' in response.headers['content-type']

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls', **parametrized(VALID_ENTITIES - {entities.TemplateKind})
    )
    def test_positive_delete_status_code(self, entity_cls):
        """Issue an HTTP DELETE request and check the returned status
        code.

        :id: bacf4bf2-eb2b-4201-a21c-8d15f5b06e7a

        :parametrized: yes

        :expectedresults: HTTP 200, 202 or 204 is returned with an
            ``application/json`` content-type.

        :CaseImportance: Critical
        """
        entity = entity_cls(id=entity_cls().create_json()['id'])
        response = entity.delete_raw()
        assert response.status_code in (
            http.client.NO_CONTENT,
            http.client.OK,
            http.client.ACCEPTED,
        )

        # According to RFC 2616, HTTP 204 responses "MUST NOT include a
        # message-body". If a message does not have a body, there is no
        # need to set the content-type of the message.
        if response.status_code is not http.client.NO_CONTENT:
            assert 'application/json' in response.headers['content-type']


class TestDoubleCheck:
    """Perform in-depth tests on URLs.

    Do not just assume that an HTTP response with a good status code indicates
    that an action succeeded. Instead, issue a follow-up request after each
    action to ensure that the intended action was accomplished.
    """

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls', **parametrized(VALID_ENTITIES - {entities.TemplateKind})
    )
    def test_positive_put_and_get_requests(self, entity_cls):
        """Update an entity, then read it back.

        :id: f5d3039f-5468-4dd2-8ac9-6e948ef39866

        :parametrized: yes

        :expectedresults: The entity is updated with the given attributes.

        :CaseImportance: Medium

        :BZ: 1378009
        """
        # Create an entity.
        entity = entity_cls().create_json()

        # Update that entity. FIXME: This whole procedure is a hack.
        kwargs = {'organization': entity['organization_id']} if 'organization_id' in entity else {}
        new_entity = entity_cls(**kwargs)
        # Generate randomized instance attributes
        new_entity.create_missing()
        response = client.put(
            entity_cls(id=entity['id']).path(),
            new_entity.create_payload(),
            auth=settings.server.get_credentials(),
            verify=False,
        )
        response.raise_for_status()

        # Compare `payload` against entity information returned by the
        # server.
        payload = _get_readable_attributes(new_entity)
        entity_attrs = entity_cls(id=entity['id']).read_json()
        for key, value in payload.items():
            assert key in entity_attrs.keys()
            assert value == entity_attrs[key]

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls', **parametrized(VALID_ENTITIES - {entities.TemplateKind})
    )
    def test_positive_post_and_get_requests(self, entity_cls):
        """Create an entity, then read it back.

        :id: c658095b-2bf9-4c3e-8ddf-c1792e743a10

        :parametrized: yes

        :expectedresults: The entity is created with the given attributes.

        :CaseImportance: Medium
        """
        entity = entity_cls()
        entity_id = entity.create_json()['id']

        # Compare `payload` against entity information returned by the
        # server.
        payload = _get_readable_attributes(entity)
        entity_attrs = entity_cls(id=entity_id).read_json()
        for key, value in payload.items():
            assert key in entity_attrs.keys()
            assert value == entity_attrs[key]

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls', **parametrized(VALID_ENTITIES - {entities.TemplateKind})
    )
    def test_positive_delete_and_get_requests(self, entity_cls):
        """Issue an HTTP DELETE request and GET the deleted entity.

        :id: 04a37ba7-c553-40e1-bc4c-ec2ebf567647

        :parametrized: yes

        :expectedresults: An HTTP 404 is returned when fetching the missing
            entity.

        :CaseImportance: Critical
        """
        # Create an entity, delete it and get it.
        entity = entity_cls(id=entity_cls().create_json()['id'])
        entity.delete()
        assert http.client.NOT_FOUND == entity.read_raw().status_code


class TestEntityRead:
    """Check whether classes inherited from
    ``nailgun.entity_mixins.EntityReadMixin`` are working properly.
    """

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls',
        **parametrized(
            VALID_ENTITIES
            - {
                entities.Architecture,  # see test_architecture_read
                entities.OperatingSystemParameter,  # see test_osparameter_read
                entities.TemplateKind,  # see comments in class definition
            }
        ),
    )
    def test_positive_entity_read(self, entity_cls):
        """Create an entity and get it using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        :id: 78bddedd-bbcf-4e26-a9f7-746874f58529

        :parametrized: yes

        :expectedresults: The just-read entity is an instance of the correct
            class.

        :CaseImportance: Critical
        """
        entity_id = entity_cls().create_json()['id']
        assert isinstance(entity_cls(id=entity_id).read(), entity_cls)

    @pytest.mark.tier1
    def test_positive_architecture_read(self):
        """Create an arch that points to an OS, and read the arch.

        :id: e4c7babe-11d8-4f85-8382-5267a49046e9

        :expectedresults: The call to ``Architecture.read`` succeeds, and the
            response contains the correct operating system ID.

        :CaseImportance: Critical
        """
        os_id = entities.OperatingSystem().create_json()['id']
        arch_id = entities.Architecture(operatingsystem=[os_id]).create_json()['id']
        architecture = entities.Architecture(id=arch_id).read()
        assert len(architecture.operatingsystem) == 1
        assert architecture.operatingsystem[0].id == os_id

    @pytest.mark.tier1
    def test_positive_syncplan_read(self):
        """Create a SyncPlan and read it back using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        :id: 2a5f53c7-262a-44a6-b7bf-d57fbaef3dc7

        :expectedresults: The just-read entity is an instance of the correct
            class.

        :CaseImportance: Critical
        """
        org_id = entities.Organization().create_json()['id']
        syncplan_id = entities.SyncPlan(organization=org_id).create_json()['id']
        assert isinstance(
            entities.SyncPlan(organization=org_id, id=syncplan_id).read(), entities.SyncPlan
        )

    @pytest.mark.tier1
    def test_positive_osparameter_read(self):
        """Create an OperatingSystemParameter and get it using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        :id: 1de63937-5ca1-4101-b4ee-4b398c66b630

        :expectedresults: The just-read entity is an instance of the correct
            class.

        :CaseImportance: Critical
        """
        os_id = entities.OperatingSystem().create_json()['id']
        osp_id = entities.OperatingSystemParameter(operatingsystem=os_id).create_json()['id']
        assert isinstance(
            entities.OperatingSystemParameter(id=osp_id, operatingsystem=os_id).read(),
            entities.OperatingSystemParameter,
        )

    @pytest.mark.tier1
    def test_positive_permission_read(self):
        """Create an Permission entity and get it using
        ``nailgun.entity_mixins.EntityReadMixin.read``.

        :id: 5631a1eb-33ff-4abe-bf01-6c8d98c47a96

        :expectedresults: The just-read entity is an instance of the correct
            class and name and resource_type fields are populated

        :CaseImportance: Critical
        """
        perm = entities.Permission().search(query={'per_page': '1'})[0]
        assert perm.name
        assert perm.resource_type

    @pytest.mark.tier1
    def test_positive_media_read(self):
        """Create a media pointing at an OS and read the media.

        :id: 67b656fe-9302-457a-b544-3addb11c85e0

        :expectedresults: The media points at the correct operating system.

        :CaseImportance: Critical
        """
        os_id = entities.OperatingSystem().create_json()['id']
        media_id = entities.Media(operatingsystem=[os_id]).create_json()['id']
        media = entities.Media(id=media_id).read()
        assert len(media.operatingsystem) == 1
        assert media.operatingsystem[0].id == os_id
