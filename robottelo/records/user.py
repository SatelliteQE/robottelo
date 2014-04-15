# -*- encoding: utf-8 -*-

"""
Module for Domain api and record implementation
"""


from robottelo.api.apicrud import ApiCrud
from robottelo.common import records
from robottelo.common.helpers import STR
from robottelo.records.organization import Organization
from robottelo.records.role import Role


CONSERVATIVE = [
    STR.alpha,
    STR.alphanumeric,
    STR.numeric
    ]


class UserApi(ApiCrud):
    """ Implementation of api for foreman domains
    """
    api_path = "/api/v2/users/"
    api_json_key = u"user"
    create_fields = [
        "login", "password", "auth_source_id",
        "admin", "mail", "firstname", "lastname",
        "organization_ids", "role_ids"]


class User(records.Record):
    """ Implementation of foreman user record
    """
    login = records.BasicPositiveField(include=CONSERVATIVE)
    password = records.BasicPositiveField(include=CONSERVATIVE)
    mail = records.EmailField()
    firstname = records.BasicPositiveField(include=CONSERVATIVE)
    lastname = records.BasicPositiveField(include=CONSERVATIVE)
    lastname = records.BasicPositiveField(include=CONSERVATIVE)
    auth_source_id = records.IntegerField(default=1)
    organization = records.ManyRelatedField(Organization, 1, 2)
    role = records.ManyRelatedField(Role, 1, 2, default=[])

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = UserApi
