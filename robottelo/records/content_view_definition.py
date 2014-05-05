# -*- encoding: utf-8 -*-

"""
Module for Content View api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.records.organization import Organization
from robottelo.api.base import request
from robottelo.api.apicrud import Task


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

    @classmethod
    def publish(cls, instance):
        """Synchronize repository

        """
        id = instance.id
        url = "/katello/api/v2/content_views/{0}/publish".format(id)
        result = request('post', path=url)
        return Task(result.json())

    @classmethod
    def promote(cls, version_id, environment_id):
        js = {'environment_id': environment_id}
        url = "/katello/api/v2/content_view_versions/{0}/promote".format(
            version_id
        )
        result = request('post', path=url, json=js)
        return Task(result.json())


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
