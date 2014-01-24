# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrud


class DomainApi(ApiCrud):
        api_path = "/api/domains/"
        api_json_key = u"domain"
        create_fields = ["name"]
