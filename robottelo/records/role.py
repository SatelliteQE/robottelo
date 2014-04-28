# -*- encoding: utf-8 -*-

"""
Module for Activation Key api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud


class FilterApi(ApiCrud):
    """
    """
    api_path = "/api/v2/filters/"

    create_fields = ["role_id", "permission_ids", "search"]


class Filter(records.Record):
    """Definition of activation key entity
    """

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = FilterApi


class RolesApi(ApiCrud):
    """Api implementation for activation keys
    """
    api_path = "/api/v2/roles/"

    create_fields = ["name"]


class Role(records.Record):
    """Definition of activation key entity
    """

    name = records.StringField(required=True)

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = RolesApi


def add_permission_to_user(user_created, perm):
    role = Role()
    created_role = ApiCrud.record_create(role)
    flter = Filter()
    flter.role_id = created_role.id
    flter.permission_ids = [perm.id]
    ApiCrud.record_create(flter)
    user_created.role_ids = [created_role.id]
    ApiCrud.record_update(user_created)
