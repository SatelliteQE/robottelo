# -*- encoding: utf-8 -*-

"""
Module for Environment api and record implementation
"""


from robottelo.api.apicrud import ApiCrud
from robottelo.common import records


class EnvironmentApi(ApiCrud):
    """ Implementation of api for  foreman environments
    """
    api_path = "/api/environments/"
    api_json_key = u"environment"
    create_fields = ["name"]


class Environment(records.Record):
    """ Implementation of foreman environments record
    """
    name = records.StringField()

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = EnvironmentApi
