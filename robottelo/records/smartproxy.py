# -*- encoding: utf-8 -*-

"""
Module for Smart proxy api an record implementation
"""


from robottelo.common import conf, records
from robottelo.api.apicrud import ApiCrud


class SmartProxyApi(ApiCrud):
    """ Implementation of api for  foreman SmartProxy
    """
    api_path = "/api/smart_proxies/"
    api_json_key = u"smart_proxy"

    create_fields = ["name",
                     "url"]


class SmartProxy(records.Record):
    """ Implementation of foreman SmartProxy record
    We asume, that main server has smart proxy configured.
    """
    name = records.StringField()
    url = records.StringField(
        default="https://" + conf.properties['main.server.hostname'])

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = SmartProxyApi
