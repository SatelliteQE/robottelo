# -*- encoding: utf-8 -*-

"""
Module for Organization api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.common.helpers import STR


LABELS = [
    STR.alpha,
    STR.alphanumeric,
    STR.numeric
    ]


class OrganizationApi(ApiCrud):
    """ Implementation of api for katello organizations
    """
    api_path = "/katello/api/v2/organizations"
    api_json_key = u"organization"
    create_fields = ["name", "label", "description"]
    update_fields = ["name", "description", 'label']


class Organization(records.Record):
    """ Implementation of katello organizaiton record
    """
    name = records.BasicPositiveField()
    label = records.BasicPositiveField(include=LABELS)
    description = records.BasicPositiveField()

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = OrganizationApi
