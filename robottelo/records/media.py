# -*- encoding: utf-8 -*-

"""
Module for Media api record implementation
"""


from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.records.operatingsystem import OperatingSystem


class MediaApi(ApiCrud):
    """ Implementation of api for  foreman media
    """
    api_path = "/api/v2/media/"
    api_json_key = u"medium"
    create_fields = ['name', 'path', 'operatingsystem_ids']


class Media(records.Record):
    """Implementation of foreman media record """
    name = records.StringField(fmt=r"media\d\d\d\d\d")
    path = records.StringField(fmt=r"https?://\w\w\w\w\w\w.com")
    operatingsystem = records.ManyRelatedField(OperatingSystem, 1, 3)

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = MediaApi
