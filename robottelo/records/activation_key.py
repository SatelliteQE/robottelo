# -*- encoding: utf-8 -*-

"""
Module for Activation Key api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.records.organization import Organization


class ActivationKeyApi(ApiCrud):
    """Api implementation for activation keys
    """
    api_path = "/katello/api/v2/activation_keys"
    create_fields = [
        "name", "label", "description", "environment_id",
        "content_view_id", "usage_limit", "organization_id"
        ]


class ActivationKey(records.Record):
    """Definition of activation key entity
    """
    name = records.basic_positive()
    description = records.basic_positive()
    organization_id = records.IntegerField(default=1)
    environment_id = records.IntegerField(default=1)
    content_view_id = records.IntegerField(default=1)
    usage_limit = records.IntegerField()

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = ActivationKeyApi
