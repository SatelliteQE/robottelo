from robottelo.api.hosts import HostApi
from robottelo.common import records
from robottelo.common.records.architectures import Architectures
from robottelo.common.records.domains import Domains
from robottelo.common.records.environments import Environments
from robottelo.common.records.operatingsystems import OperatingSystems
from robottelo.common.records.smart_proxies import SmartProxies


def after_generating(instance):
    return instance


class Hosts(records.Record):
    name = records.StringField(format=r"host_\d\d\d\d\d", required=True)
    mac = records.MACField(required=True)
    environment = records.RelatedField(Environments)
    architecture = records.RelatedField(Architectures)
    domain = records.RelatedField(Domains)
    puppet_proxy = records.RelatedField(SmartProxies)
    operatingsystem = records.RelatedField(OperatingSystems)

    class Meta:
        api_class = HostApi
