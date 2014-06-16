# -*- encoding: utf-8 -*-

"""
Module for Environment api and record implementation
"""


from robottelo.records.organization import Organization
from robottelo.api.apicrud import ApiCrud
from robottelo.common import records


class EnvironmentKatelloApi(ApiCrud):
    """ Implementation of api for  foreman environments
    """
    api_path = "/katello/api/v2/organizations/:organization.id/environments/"
    api_json_key = u"environment"
    create_fields = ["name", "organization_id", "label", "prior"]


class EnvironmentKatello(records.Record):
    """ Implementation of foreman environments record
    """
    name = records.StringField()
    label = records.StringField()
    prior = records.IntegerField(min_=1, max_=1)
    organization = records.RelatedField(Organization)

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = EnvironmentKatelloApi


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
