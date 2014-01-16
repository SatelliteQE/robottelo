from robottelo.common import models
from robottelo.api.smart_proxies import SmartProxyApi

from robottelo.common import conf

class SmartProxies(models.Model):
    name = models.StringField(required=True)
    url = models.StringField(default=conf.properties['main.server.hostname'], required=True)

    class Meta:
        api_class = SmartProxyApi
