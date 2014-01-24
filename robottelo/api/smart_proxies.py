# -*- encoding: utf-8 -*-


from robottelo.api.apicrud import ApiCrud


class SmartProxyApi(ApiCrud):
        api_path = "/api/smart_proxies/"
        api_json_key = u"smart_proxy"

        create_fields = ["name",
                         "url"]
