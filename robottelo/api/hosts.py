# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrud


class HostApi(ApiCrud):
        api_path = "/api/hosts/"
        api_json_key = u"host"
        create_fields = ["name",
                         "environment_id",
                         "architecture_id",
                         "root_pass",
                         "mac",
                         "domain_id",
                         "puppet_proxy_id",
                         "ptable_id",
                         "operatingsystem_id"]
