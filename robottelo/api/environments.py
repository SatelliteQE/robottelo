# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrud


class EnvironmentApi(ApiCrud):
        api_path = "/api/environments/"
        api_json_key = u"environment"
        create_fields = ["name"]
