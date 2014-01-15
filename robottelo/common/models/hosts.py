from robottelo.common import models
from robottelo.common.models.environments import Environments
from robottelo.common.models.architectures import Architectures
from robottelo.common.models.domains import Domains
from robottelo.common.models.smart_proxies import SmartProxies
from robottelo.common.models.operatingsystems import OperatingSystems
from robottelo.api.hosts import HostApi

def after_generating(instance):
    return instance

class Hosts(models.Model):
    name = models.StringField(format=r"host_\d\d\d\d\d",required=True)
    mac = MACField(required=True)
    environment = models.RecordField(Environments)
    architecture = models.RecordField(Architectures)
    domain = models.RecordField(Domains)
    puppet_proxy = models.RecordField(SmartProxies)
    operatingsystem = models.RecordField(OperatingSystems)


    class Meta:
        api_class = HostApi
