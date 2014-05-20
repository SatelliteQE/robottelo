# -*- encoding: utf-8 -*-

"""
Module for Activation Key api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.api.base import request


class ActivationKeyApi(ApiCrud):
    """Api implementation for activation keys
    """
    api_path = "/katello/api/v2/activation_keys"
    create_fields = [
        "name", "label", "description", "environment_id",
        "content_view_id", "usage_limit", "organization_id"
        ]

    @classmethod
    def add_host_collection(cls, instance, host_collection_ids):
        """Add host collections to an activation key record"""

        url = "/katello/api/v2/activation_keys/{}/host_collections".format(
            instance.id)
        return request(
            'put',
            path=url,
            json={
                'activation_key': {
                    'host_collection_ids': host_collection_ids
                },
            })


class ActivationKey(records.Record):
    """Definition of activation key entity
    """
    name = records.BasicPositiveField()
    description = records.BasicPositiveField()
    organization_id = records.Field(default=1)
    environment_id = records.IntegerField(default=1)
    content_view_id = records.IntegerField(default=1)
    usage_limit = records.IntegerField()

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = ActivationKeyApi
