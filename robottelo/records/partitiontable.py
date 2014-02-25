# -*- encoding: utf-8 -*-

"""
Module for Partition Table api an record implementation
"""


from robottelo.common import records
from robottelo.common.constants import OPERATING_SYSTEMS
from robottelo.records.operatingsystem import OperatingSystem
from robottelo.api.apicrud import ApiCrud


class PTableApi(ApiCrud):
    """ Implementation of api for  foreman partition tables
    """
    api_path = "/api/ptables/"
    api_json_key = u"ptable"

    create_fields = ["name",
                     "layout",
                     "operatingsystem_ids",
                     "os_family"]


class PartitionTable(records.Record):
    """ Implementation of foreman partition table record
    """
    name = records.StringField()
    layout = records.StringField(default="d-i partman-auto/disk")
    operatingsystem = records.ManyRelatedField(OperatingSystem, 1, 3)
    os_family = records.ChoiceField(OPERATING_SYSTEMS)

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = PTableApi
