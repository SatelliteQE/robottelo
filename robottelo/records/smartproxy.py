from robottelo.api.smart_proxies import SmartProxyApi
from robottelo.common import conf, records


class SmartProxy(records.Record):
    name = records.StringField()
    url = records.StringField(
            default="https://" + conf.properties['main.server.hostname'])

    class Meta:
        api_class = SmartProxyApi
