# -*- encoding: utf-8 -*-

"""
Module for Content View api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.records.organization import Organization
from robottelo.api.base import request
from robottelo.records.permission import PermissionList


class ContentViewDefinitionApi(ApiCrud):
    """Content view api implementation utilizes :organization.label,
    what means, that create requires initialize organization object.
    """
    api_path = "/katello/api/v2/organizations/:organization.label/content_views/"  # noqa
    api_path_get = "/katello/api/v2/content_views/"  # noqa
    api_path_put = "/katello/api/v2/content_views/"  # noqa
    api_path_delete = "/katello/api/v2/content_views/"  # noqa
    api_json_key = u"content_view"
    create_fields = ["name", "description", "organization_id", "composite"]

    permissions = PermissionList("content_views")

    @classmethod
    def publish(cls, instance):
        """Synchronize repository

        """
        id = instance.id
        url = "/katello/api/v2/content_views/{0}/publish".format(id)
        result = request('post', path=url)
        return result.json()


class ContentViewDefinition(records.Record):
    """ Implementation of kattelo content view definition record
    """
    name = records.BasicPositiveField()
    description = records.BasicPositiveField()
    organization = records.RelatedField(Organization)

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = ContentViewDefinitionApi
