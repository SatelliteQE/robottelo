# -*- encoding: utf-8 -*-

"""
Module for Domain api and record implementation
"""


from robottelo.api.apicrud import ApiCrud
from robottelo.common import records
from robottelo.records.permission import PermissionList


class DomainApi(ApiCrud):
    """ Implementation of api for foreman domains
    """
    api_path = "/api/domains/"
    api_json_key = u"domain"
    create_fields = ["name"]

    permissions = PermissionList("domains")


class Domain(records.Record):
    """ Implementation of foreman domains record
    """
    name = records.StringField(format=r"domain\d\d\d\d")

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = DomainApi
        change_for_update = lambda i: i.record_set_field(
            name=i.name+".uk"
            )
