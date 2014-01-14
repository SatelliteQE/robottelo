# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrudMixin


class OperatingSystemApi(ApiCrudMixin):
        api_path = "/api/operatingsystems"
        api_json_key = u"operatingsystem"
