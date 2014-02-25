# -*- encoding: utf-8 -*-

"""
Module for Operating System api an record implementation
"""


from robottelo.common import records
from robottelo.common.helpers import valid_names_list
from robottelo.common.constants import OPERATING_SYSTEMS
from robottelo.api.apicrud import ApiCrud


class OperatingSystemApi(ApiCrud):
        api_path = "/api/operatingsystems"
        api_json_key = u"operatingsystem"

        create_fields = ["name",
                         "major",
                         "minor",
                         "family",
                         "release_name"]


class OperatingSystem(records.Record):
    name = records.ChoiceField(valid_names_list())
    major = records.IntegerField()
    minor = records.IntegerField()
    family = records.ChoiceField(OPERATING_SYSTEMS)
    release_name = records.StringField(r"osrelease\d\d\d")

    class Meta:
        api_class = OperatingSystemApi
