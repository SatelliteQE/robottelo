# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrudMixin


class HostApi(ApiCrudMixin):
        api_path = "/api/hosts/"
        api_json_key = u"host"
        create_fields = ["name",
                         "environment_id",
                         "architecture_id",
                         "domain_id",
                         "puppet_proxy_id",
                         "operatingsystem_id"]
