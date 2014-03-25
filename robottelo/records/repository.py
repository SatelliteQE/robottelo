# -*- encoding: utf-8 -*-

"""
Module for Activation Key api an record implementation
"""

from robottelo.common import records
from robottelo.api.apicrud import ApiCrud, Task
from robottelo.records.product import CustomProduct
from robottelo.api.base import request


class CustomRepositoryApi(ApiCrud):
    """Api implementation for activation keys
    """
    api_path = "/katello/api/v2/repositories/"  # noqa
    create_fields = [
        "name", "description", "product_id",
        "url", "enabled", "content_type"
        ]

    @classmethod
    def synchronize(cls, instance):
        """Synchronize repository
        """
        id = instance.id
        url = "/katello/api/v2/repositories/{0}/sync".format(id)
        result = request('post', path=url)
        return Task(result.json())


class CustomRepository(records.Record):
    """Definition of activation key entity
    """
    name = records.basic_positive()
    description = records.basic_positive()
    product = records.RelatedField(CustomProduct)
    url = records.StringField(
        default="http://inecas.fedorapeople.org/fakerepos/zoo/"
        )
    enabled = records.Field(default=True)
    content_type = records.StringField(default="yum")

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = CustomRepositoryApi
