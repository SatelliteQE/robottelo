# -*- encoding: utf-8 -*-

"""
Module for Product api record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.records.organization import Organization


class ProductApi(ApiCrud):
    """Api implementation for activation keys
    """
    api_path = "/katello/api/v2/products/"
    create_fields = [
        "name", "label", "description", "organization_id"
        ]


class CustomProduct(records.Record):
    """Definition of product key entity
    """
    name = records.BasicPositiveField()
    description = records.BasicPositiveField()
    organization = records.RelatedField(Organization)

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = ProductApi
