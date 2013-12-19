# -*- encoding: utf-8 -*-
from random import randint, choice
from robottelo.api.apicrud import ApiCrudMixin
from robottelo.api.model import ApiModelMixin
from robottelo.common.helpers import generate_name
from robottelo.common.helpers import generate_email_address


class OperatingSystemApi(ApiCrudMixin, ApiModelMixin):
    """Implementation of /api/operatingsystems endpoint"""
    @classmethod
    def api_path(cls):
        return "/api/operatingsystems/"

    @classmethod
    def id_from_json(cls, json):
        return json[u'operatingsystem'][u'id']

    def __init__(self, generate=False):
        if generate:
            self.name = unicode(generate_name(8))
            self.major = unicode(randint(1, 8))
            self.minor = unicode(randint(1, 30))
            self.family = unicode(choice(
                ["Archlinux",
                "Debian",
                "Freebsd",
                "Gentoo",
                "Redhat",
                "Solaris",
                "Suse",
                "Windows"]))
            self.release_name = unicode(generate_name(8))

    def opts(self):
        return {u'operatingsystem': self.to_data_structure()}

    def change(self):
        self.release_name += "updated"
        return self
