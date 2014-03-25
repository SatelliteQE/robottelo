# -*- encoding: utf-8 -*-

"""
Module for Activation Key api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.records.organization import Organization


class ProductApi(ApiCrud):
    """Api implementation for activation keys
    """
    api_path = "/katello/api/v2/products/"  # noqa
    create_fields = [
        "name", "label", "description", "organization_id"
        ]


class CustomProduct(records.Record):
    """Definition of activation key entity
    """
    name = records.basic_positive()
    description = records.basic_positive()
    organization = records.RelatedField(Organization, record_label=True)

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = ProductApi
