# -*- encoding: utf-8 -*-

"""
Module for Arcitecture api and record implementation
"""


from robottelo.api.apicrud import ApiCrud
from robottelo.common import records
from robottelo.records.operatingsystem import OperatingSystem
from robottelo.records.permission import PermissionList


class ArchitectureApi(ApiCrud):
    """Implementation of Architecture api"""
    api_path = "/api/v2/architectures"
    api_json_key = u"architecture"
    create_fields = ["name", "operatingsystem_ids"]

    permissions = PermissionList("architectures")


class Architecture(records.Record):
    """Definition of architecture entity"""
    name = records.StringField(required=True)
    operatingsystem = records.ManyRelatedField(OperatingSystem, 1, 3)

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = ArchitectureApi
        change_for_update = lambda i: i.record_set_field(
            name="%s_updated" % i.name
            )
