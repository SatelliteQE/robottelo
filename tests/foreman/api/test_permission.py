# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai


from ddt import ddt
from robottelo.common.decorators import data
from tests.foreman.api.baseapi import BaseAPI
from robottelo.records.domain import Domain
from robottelo.records.architecture import Architecture
from robottelo.records.user import User
from robottelo.records.role import Filter
from robottelo.records.role import Role
from robottelo.api.apicrud import ApiCrud


def add_permission_to_user(user_created, perm):
    role = Role()
    created_role = ApiCrud.record_create(role)
    flter = Filter()
    flter.role_id = created_role.id
    flter.permission_ids = [perm.id]
    ApiCrud.record_create(flter)
    user_created.role_ids = [created_role.id]
    ApiCrud.record_update(user_created)


@ddt
class TestPermission(BaseAPI):
    """Testing basic positive permissions"""

    @data(Domain, Architecture)
    def test_basic_create(self, test_data):
        """
        @feature: Permissions
        @test: try to create entity first with relevant permissionn
        @assert: entity is created
        """

        entity = test_data()
        deps = ApiCrud.record_create_dependencies(entity)

        user_definition = User()
        user_created = ApiCrud.record_create_recursive(user_definition)

        # user doesn't yet have relevant permission, action should fail
        with self.assertRaises(Exception):
            ApiCrud.record_create(deps, user_definition)

        perm = ApiCrud.record_resolve(
            test_data._meta.api_class.permissions.create
            )
        add_permission_to_user(user_created, perm)
        # user should have the relevant permission, action should work
        created = ApiCrud.record_create(deps, user_definition)
        self.assertIntersects(deps, created)

    @data(Domain, Architecture)
    def test_basic_read(self, test_data):
        """
        @feature: Permissions
        @test: try to read entity first with relevant permissionn
        @assert: entity is created
        """
        entity = test_data()
        created = ApiCrud.record_create_recursive(entity)

        user_definition = User()
        user_created = ApiCrud.record_create_recursive(user_definition)

        # user doesn't yet have relevant permission, action should fail
        with self.assertRaises(Exception):
            ApiCrud.record_resolve(created, user_definition)

        perm = ApiCrud.record_resolve(
            test_data._meta.api_class.permissions.resolve
            )
        add_permission_to_user(user_created, perm)
        # user should have the relevant permission, action should work
        eres = ApiCrud.record_resolve(created, user_definition)
        self.assertIntersects(eres, created)

    @data(Domain, Architecture)
    def test_basic_remove(self, test_data):
        """
        @feature: Permissions
        @test: try to remove entity first with relevant permissionn
        @assert: entity is removed
        """
        entity = test_data()
        created = ApiCrud.record_create_recursive(entity)

        user_definition = User()
        user_created = ApiCrud.record_create_recursive(user_definition)

        # user doesn't yet have relevant permission, action should fail
        with self.assertRaises(Exception):
            ApiCrud.record_remove(created, user_definition)

        perm = ApiCrud.record_resolve(
            test_data._meta.api_class.permissions.remove
            )
        add_permission_to_user(user_created, perm)
        # user should have the relevant permission, action should work
        ApiCrud.record_remove(created, user_definition)
        self.assertFalse(ApiCrud.record_exists(created))

    @data(Domain, Architecture)
    def test_basic_update(self, test_data):
        """
        @feature: Permissions
        @test: try to update entity first with relevant permissionn
        @assert: entity is removed
        """
        entity = test_data()
        created = ApiCrud.record_create_recursive(entity)

        created = test_data._meta.change_for_update(created)
        user_definition = User()
        user_created = ApiCrud.record_create_recursive(user_definition)

        # user doesn't yet have relevant permission, action should fail
        with self.assertRaises(Exception):
            ApiCrud.record_update(created, user_definition)

        perm = ApiCrud.record_resolve(
            test_data._meta.api_class.permissions.update
            )
        add_permission_to_user(user_created, perm)
        # user should have the relevant permission, action should
        updated = ApiCrud.record_update(created, user_definition)
        del created["updated_at"]
        del updated["updated_at"]
        self.assertIntersects(created, updated)
