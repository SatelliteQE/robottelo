# -*- encoding: utf-8 -*-

"""
Module for Activation Key api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.records.organization import Organization
from robottelo.records.environment import Environment
from robottelo.records.content_view_definition import ContentViewDefinition


class ActivationKeyApi(ApiCrud):
    """Api implementation for activation keys
    """
    api_path = "/katello/api/activation_keys/"  # noqa
    api_json_key = u"activation_key"
    create_fields = [
        "name", "label", "description", "environment_id",
        "content_view_id", "usage_limit"
        ]


class ActivationKey(records.Record):
    """Definition of activation key entity
    """
    name = records.basic_positive()
    description = records.basic_positive()
    organization = records.RelatedField(Organization)
    environment = records.RelatedField(Environment)
    content_view = records.RelatedField(ContentViewDefinition)
    usage_limit = records.IntegerField()

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = ActivationKeyApi
