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
    def add_sysgroups(cls, instance, group_ids):
        """Add sysgroups
        """
        i = instance.id
        url = "/katello/api/v2/activation_keys/{0}/system_groups".format(i)
        return request(
            'post',
            path=url,
            json={'activation_key': {'system_group_ids': group_ids}})


class ActivationKey(records.Record):
    """Definition of activation key entity
    """
    name = records.BasicPositiveField()
    description = records.BasicPositiveField()
    organization_id = records.IntegerField(default=1)
    environment_id = records.IntegerField(default=1)
    content_view_id = records.IntegerField(default=1)
    usage_limit = records.IntegerField()

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = ActivationKeyApi
