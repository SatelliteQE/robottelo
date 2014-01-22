# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrudMixin


class PTableApi(ApiCrudMixin):
        api_path = "/api/ptables/"
        api_json_key = u"ptable"

        create_fields = ["name",
                         "layout",
                         "operatingsystem_ids",
                         "os_family"]
