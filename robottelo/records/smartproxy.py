from robottelo.common import conf, records
from robottelo.api.apicrud import ApiCrud


class SmartProxyApi(ApiCrud):
        api_path = "/api/smart_proxies/"
        api_json_key = u"smart_proxy"

        create_fields = ["name",
                         "url"]


class SmartProxy(records.Record):
    name = records.StringField()
    url = records.StringField(
        default="https://" + conf.properties['main.server.hostname'])

    class Meta:
        api_class = SmartProxyApi
