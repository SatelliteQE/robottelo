# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrudMixin


class EnvironmentApi(ApiCrudMixin):
        api_path = "/api/environments/"
        api_json_key = u"environment"
        create_fields = ["name"]
