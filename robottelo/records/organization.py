# -*- encoding: utf-8 -*-

"""
Module for Organization api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.common.helpers import STR


label_include = [
    STR.alpha,
    STR.alphanumeric,
    STR.numeric
    ]


class OrganizationApi(ApiCrud):
    api_path = "/katello/api/organizations/"
    api_json_key = u"organization"
    create_fields = ["name", "label", "description"]


class Organization(records.Record):
    name = records.basic_positive()
    label = records.basic_positive(include=label_include)
    description = records.basic_positive()

    class Meta:
        api_class = OrganizationApi
