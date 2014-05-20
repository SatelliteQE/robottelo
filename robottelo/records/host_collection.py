# -*- encoding: utf-8 -*-

"""
Module for Host Collections api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud


class HostCollectionApi(ApiCrud):
    """Api implementation for Host Collections
    """
    api_path = "/katello/api/v2/host_collections"
    create_fields = [
        "name", "description",
        "organization_id", "system_ids", "max_systems"
        ]


class HostCollectionDefOrg(records.Record):
    """Definition of Host Collections entity
    """
    name = records.BasicPositiveField()
    description = records.BasicPositiveField()
    organization_id = records.IntegerField(default=1)
    max_systems = records.IntegerField()

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = HostCollectionApi
