# -*- encoding: utf-8 -*-
from robottelo.api.apicrud import ApiCrudMixin
from robottelo.api.model import ApiModelMixin
from robottelo.common.helpers import generate_name
from robottelo.common.helpers import generate_email_address


class UserApi(ApiCrudMixin, ApiModelMixin):
    """Implementation of /api/user endpoint"""
    @classmethod
    def api_path(cls):
        return "/api/users/"

    @classmethod
    def id_from_json(cls, json):
        return json[u'user'][u'id']

    def __init__(self, generate=False):
        if generate:
            self.login = unicode(generate_name(6))
            self.password = unicode(generate_name(8))
            self.mail = unicode(generate_email_address())
            self.firstname = unicode(generate_name(6))
            self.lastname = unicode(generate_name(6))
            self.admin = False
            self.auth_source_id = 1

    def opts(self):
        return {u'user': self.to_data_structure()}

    def result_opts(self):
        return self.graylist(password=False).opts()

    def change(self):
        self.mail = "updated" + self.mail
        return self

