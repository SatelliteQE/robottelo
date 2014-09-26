# -*- encoding: utf-8 -*-

"""
Module for Activation Key api an record implementation
"""

from robottelo.api.apicrud import ApiCrud, Task
from robottelo.api.base import request
from robottelo.common import records
from robottelo.common.constants import FAKE_1_YUM_REPO
from robottelo.records.product import CustomProduct


class CustomRepositoryApi(ApiCrud):
    """Api implementation for activation keys
    """
    api_path = "/katello/api/v2/repositories"
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
    name = records.BasicPositiveField()
    description = records.BasicPositiveField()
    product = records.RelatedField(CustomProduct)
    url = records.StringField(
        default=FAKE_1_YUM_REPO
        )
    enabled = records.Field(default=True)
    content_type = records.StringField(default="yum")

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = CustomRepositoryApi
