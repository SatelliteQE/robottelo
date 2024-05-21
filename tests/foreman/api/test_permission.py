"""Unit tests for the ``permissions`` paths.

Each class tests a single URL. A full list of URLs to be tested can be found on your satellite:
http://<satellite-host>/apidoc/v2/permissions.html


:Requirement: Permission

:CaseAutomation: Automated

:CaseComponent: UsersRoles

:Team: Endeavour

:CaseImportance: High

"""

from itertools import chain
import json
import re

from fauxfactory import gen_alphanumeric
from nailgun import entities
from nailgun.entity_fields import OneToManyField
import pytest
from requests.exceptions import HTTPError

from robottelo.config import user_nailgun_config
from robottelo.constants import PERMISSIONS
from robottelo.utils.datafactory import parametrized


class TestPermission:
    """Tests for the ``permissions`` path."""

    @pytest.fixture(scope='class', autouse=True)
    def create_permissions(self, class_target_sat):
        # workaround for setting class variables
        cls = type(self)
        cls.permissions = PERMISSIONS.copy()
        if class_target_sat.is_upstream:
            cls.permissions[None].extend(cls.permissions.pop('DiscoveryRule'))
            cls.permissions[None].remove('app_root')
            cls.permissions[None].remove('attachments')
            cls.permissions[None].remove('configuration')
            cls.permissions[None].remove('logs')
            cls.permissions[None].remove('view_cases')
            cls.permissions[None].remove('view_log_viewer')

        result = class_target_sat.execute('rpm -qa | grep rubygem-foreman_openscap')
        if result.status != 0:
            cls.permissions.pop('ForemanOpenscap::Policy')
            cls.permissions.pop('ForemanOpenscap::ScapContent')
            cls.permissions[None].remove('destroy_arf_reports')
            cls.permissions[None].remove('view_arf_reports')
            cls.permissions[None].remove('create_arf_reports')
        result = class_target_sat.execute('rpm -qa | grep rubygem-foreman_remote_execution')
        if result.status != 0:
            cls.permissions.pop('JobInvocation')
            cls.permissions.pop('JobTemplate')
            cls.permissions.pop('RemoteExecutionFeature')
            cls.permissions.pop('TemplateInvocation')

        #: e.g. ['Architecture', 'Audit', 'AuthSourceLdap', …]
        cls.permission_resource_types = list(cls.permissions.keys())
        #: e.g. ['view_architectures', 'create_architectures', …]
        cls.permission_names = list(chain.from_iterable(cls.permissions.values()))

    @pytest.mark.tier1
    def test_positive_search_by_name(self, target_sat):
        """Search for a permission by name.

        :id: 1b6117f6-599d-4b2d-80a8-1e0764bdc04d

        :expectedresults: Only one permission is returned, and the permission
            returned is the one searched for.

        :CaseImportance: Critical
        """
        failures = {}
        for permission_name in self.permission_names:
            results = target_sat.api.Permission().search(
                query={'search': f'name="{permission_name}"'}
            )
            if len(results) != 1 or len(results) == 1 and results[0].name != permission_name:
                failures[permission_name] = {
                    'length': len(results),
                    'returned_names': [result.name for result in results],
                }

        if failures:
            pytest.fail(json.dumps(failures, indent=True, sort_keys=True))

    @pytest.mark.tier1
    def test_positive_search_by_resource_type(self, target_sat):
        """Search for permissions by resource type.

        :id: 29d9362b-1bf3-4722-b40f-a5e8b4d0d9ba

        :expectedresults: The permissions returned are equal to what is listed
            for that resource type in :data:`robottelo.constants.PERMISSIONS`.

        :CaseImportance: Critical
        """
        failures = {}
        for resource_type in self.permission_resource_types:
            if resource_type is None:
                continue
            perm_group = target_sat.api.Permission().search(
                query={'search': f'resource_type="{resource_type}"'}
            )
            permissions = {perm.name for perm in perm_group}
            expected_permissions = set(self.permissions[resource_type])
            added = tuple(permissions - expected_permissions)
            removed = tuple(expected_permissions - permissions)

            if added or removed:
                failures[resource_type] = {}
            if added or removed:
                failures[resource_type]['added'] = added
            if removed:
                failures[resource_type]['removed'] = removed

        if failures:
            pytest.fail(json.dumps(failures, indent=True, sort_keys=True))

    @pytest.mark.tier1
    def test_positive_search(self, target_sat):
        """search with no parameters return all permissions

        :id: e58308df-19ec-415d-8fa1-63ebf3cd0ad6

        :expectedresults: Search returns a list of all expected permissions

        :CaseImportance: Critical
        """
        permissions = target_sat.api.Permission().search(query={'per_page': '1000'})
        names = {perm.name for perm in permissions}
        resource_types = {perm.resource_type for perm in permissions}
        expected_names = set(self.permission_names)
        expected_resource_types = set(self.permission_resource_types)

        added_resource_types = tuple(resource_types - expected_resource_types)
        removed_resource_types = tuple(expected_resource_types - resource_types)
        added_names = tuple(names - expected_names)
        removed_names = tuple(expected_names - names)

        diff = {}
        if added_resource_types:
            diff['added_resource_types'] = added_resource_types
        if removed_resource_types:
            diff['removed_resource_types'] = removed_resource_types
        if added_names:
            diff['added_names'] = added_names
        if removed_names:
            diff['removed_names'] = removed_names

        if diff:
            pytest.fail(json.dumps(diff, indent=True, sort_keys=True))


# FIXME: This method is a hack. This information should somehow be tied
# directly to the `Entity` classes.
def _permission_name(entity, which_perm):
    """Find a permission name.

    Attempt to locate a permission in :data:`robottelo.constants.PERMISSIONS`.
    For example, return 'view_architectures' if ``entity`` is ``Architecture``
    and ``which_perm`` is 'read'.

    :param entity: A ``nailgun.entity_mixins.Entity`` subclass.
    :param str which_perm: Either the word "create", "read", "update" or
        "delete".
    :raise: ``LookupError`` if a relevant permission cannot be found, or if
        multiple results are found.
    """
    pattern = {'create': '^create_', 'delete': '^destroy_', 'read': '^view_', 'update': '^edit_'}[
        which_perm
    ]
    perm_names = []
    permissions = PERMISSIONS.get(entity.__name__) or PERMISSIONS.get(f'Katello::{entity.__name__}')
    for permission in permissions:
        match = re.match(pattern, permission)
        if match is not None:
            perm_names.append(permission)
    if len(perm_names) != 1:
        raise LookupError(f'Could not find the requested permission. Found: {perm_names}')
    return perm_names[0]


# This class might better belong in module test_multiple_paths.
class TestUserRole:
    """Give a user various permissions and see if they are enforced."""

    @pytest.fixture(autouse=True)
    def create_user(self, target_sat, class_org, class_location):
        """Create a set of credentials and a user."""
        self.cfg = user_nailgun_config(gen_alphanumeric(), gen_alphanumeric())
        self.user = target_sat.api.User(
            login=self.cfg.auth[0],
            password=self.cfg.auth[1],
            organization=[class_org],
            location=[class_location],
        ).create()

    def give_user_permission(self, perm_name, target_sat):
        """Give ``self.user`` the ``perm_name`` permission.

        This method creates a role and filter to accomplish the above goal.
        When complete, the relevant relationhips look like this:

            user → role ← filter → permission

        :param str perm_name: The name of a permission. For example:
            'create_architectures'.
        :raises: ``AssertionError`` if more than one permission is found when
            searching for the permission with name ``perm_name``.
        :raises: ``requests.exceptions.HTTPError`` if an error occurs when
            updating ``self.user``'s roles.
        :return: Nothing.
        """
        role = target_sat.api.Role().create()
        permissions = target_sat.api.Permission().search(query={'search': f'name="{perm_name}"'})
        assert len(permissions) == 1
        target_sat.api.Filter(permission=permissions, role=role).create()
        self.user.role += [role]
        self.user = self.user.update(['role'])

    def set_taxonomies(self, entity, organization=None, location=None):
        """Set organization and location for entity if it supports them.

        Only administrator can choose empty taxonomies or taxonomies that
        they aren't assigned to, other users can select only taxonomies they
        are granted to assign and they can't leave the selection empty.

        :param entity: Initialised nailgun's Entity object
        :param organization: Organization object or id
        :param location: Location object or id
        :return: nailgun's Entity object with updated fields
        """
        entity_fields = entity.get_fields()
        if 'organization' in entity_fields:
            if isinstance(entity_fields['organization'], OneToManyField):
                entity.organization = [organization]
            else:
                entity.organization = organization
        if 'location' in entity_fields:
            if isinstance(entity_fields['location'], OneToManyField):
                entity.location = [location]
            else:
                entity.location = location
        return entity

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls',
        **parametrized([entities.Architecture, entities.Domain, entities.ActivationKey]),
    )
    def test_positive_check_create(self, entity_cls, class_org, class_location, target_sat):
        """Check whether the "create_*" role has an effect.

        :id: e4c92365-58b7-4538-9d1b-93f3cf51fbef

        :parametrized: yes

        :expectedresults: A user cannot create an entity when missing the
            "create_*" role, and they can create an entity when given the
            "create_*" role.

        :CaseImportance: Critical

        :BZ: 1464137
        """
        with pytest.raises(HTTPError):
            entity_cls(self.cfg).create()
        self.give_user_permission(_permission_name(entity_cls, 'create'), target_sat)
        new_entity = self.set_taxonomies(entity_cls(self.cfg), class_org, class_location)
        # Entities with both org and loc require
        # additional permissions to set them.
        fields = {'organization', 'location'}
        if fields.issubset(set(new_entity.get_fields())):
            self.give_user_permission('assign_organizations', target_sat)
            self.give_user_permission('assign_locations', target_sat)
        new_entity = new_entity.create_json()
        entity_cls(id=new_entity['id']).read()  # As admin user.

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls',
        **parametrized([entities.Architecture, entities.Domain, entities.ActivationKey]),
    )
    def test_positive_check_read(self, entity_cls, class_org, class_location, target_sat):
        """Check whether the "view_*" role has an effect.

        :id: 55689121-2646-414f-beb1-dbba5973c523

        :parametrized: yes

        :expectedresults: A user cannot read an entity when missing the
            "view_*" role, and they can read an entity when given the "view_*"
            role.


        :CaseImportance: Critical
        """
        new_entity = self.set_taxonomies(entity_cls(), class_org, class_location)
        new_entity = new_entity.create()
        with pytest.raises(HTTPError):
            entity_cls(self.cfg, id=new_entity.id).read()
        self.give_user_permission(_permission_name(entity_cls, 'read'), target_sat)
        entity_cls(self.cfg, id=new_entity.id).read()

    @pytest.mark.upgrade
    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls',
        **parametrized([entities.Architecture, entities.Domain, entities.ActivationKey]),
    )
    def test_positive_check_delete(self, entity_cls, class_org, class_location, target_sat):
        """Check whether the "destroy_*" role has an effect.

        :id: 71365147-51ef-4602-948f-78a5e78e32b4

        :parametrized: yes

        :expectedresults: A user cannot read an entity with missing the
            "destroy_*" role, and they can read an entity when given the
            "destroy_*" role.


        :CaseImportance: Critical
        """
        new_entity = self.set_taxonomies(entity_cls(), class_org, class_location)
        new_entity = new_entity.create()
        with pytest.raises(HTTPError):
            entity_cls(self.cfg, id=new_entity.id).delete()
        self.give_user_permission(_permission_name(entity_cls, 'delete'), target_sat)
        entity_cls(self.cfg, id=new_entity.id).delete()
        with pytest.raises(HTTPError):
            new_entity.read()  # As admin user

    @pytest.mark.tier1
    @pytest.mark.parametrize(
        'entity_cls',
        **parametrized([entities.Architecture, entities.Domain, entities.ActivationKey]),
    )
    def test_positive_check_update(self, entity_cls, class_org, class_location, target_sat):
        """Check whether the "edit_*" role has an effect.

        :id: b5de2115-b031-413e-8e5b-eac8cb714174

        :parametrized: yes

        :expectedresults: A user cannot update an entity when missing the
            "edit_*" role, and they can update an entity when given the
            "edit_*" role.

        NOTE: This method will only work if ``entity`` has a name.


        :CaseImportance: Critical
        """
        new_entity = self.set_taxonomies(entity_cls(), class_org, class_location)
        new_entity = new_entity.create()
        name = new_entity.get_fields()['name'].gen_value()
        with pytest.raises(HTTPError):
            entity_cls(self.cfg, id=new_entity.id, name=name).update(['name'])
        self.give_user_permission(_permission_name(entity_cls, 'update'))
        # update() calls read() under the hood, which triggers
        # permission error
        entity_cls(self.cfg, id=new_entity.id, name=name).update_json(['name'])
