# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrudMixin


class SmartProxyApi(ApiCrudMixin):
        api_path = "/api/smart_proxies/"
        api_json_key = u"smart_proxy"

        create_fields = ["name",
                         "url"]
