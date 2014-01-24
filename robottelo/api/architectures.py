# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrud


class ArchitectureApi(ApiCrud):
       api_path = "/api/architectures/"
       api_json_key = u"architecture"
       create_fields = ["name", "operatingsystem_ids"]
