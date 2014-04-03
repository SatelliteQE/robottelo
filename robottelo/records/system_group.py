# -*- encoding: utf-8 -*-

"""
Module for Activation Key api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud


class SystemGroupApi(ApiCrud):
    """Api implementation for activation keys
    """
    api_path = "/katello/api/v2/system_groups"
    create_fields = [
        "name", "description",
        "organization_id", "system_ids", "max_systems"
        ]


class SystemGroupDefOrg(records.Record):
    """Definition of activation key entity
    """
    name = records.BasicPositiveField()
    description = records.BasicPositiveField()
    organization_id = records.StringField(default="ACME_Corporation")
    max_systems = records.IntegerField()

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = SystemGroupApi
