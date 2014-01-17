from robottelo.common import records
from robottelo.api.smart_proxies import SmartProxyApi

from robottelo.common import conf

class SmartProxies(records.Record):
    name = records.StringField(required=True)
    url = records.StringField(default=conf.properties['main.server.hostname'], required=True)

    class Meta:
        api_class = SmartProxyApi
