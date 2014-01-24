from robottelo.api.hosts import HostApi
from robottelo.common import records
from robottelo.common.records.environments import Environments
from robottelo.common.records.architectures import Architectures
from robottelo.common.records.domains import Domains
from robottelo.common.records.smart_proxies import SmartProxies
from robottelo.common.records.operatingsystems import OperatingSystems
from robottelo.common.records.ptables import PTables

class Hosts(records.Record):
    name = records.StringField(format=r"host_\d\d\d\d\d", required=True)
    mac = records.MACField(required=True)
    environment = records.RelatedField(Environments,required=True)
    architecture = records.RelatedField(Architectures,required=True)
    domain = records.RelatedField(Domains,required=True)
    puppet_proxy = records.RelatedField(SmartProxies,required=True)
    operatingsystem = records.RelatedField(OperatingSystems,required=True)
    ptable = records.RelatedField(PTables,required=True)

    def _post_init(self):
        self.name = self.name + "." + self.domain.name
        self.architecture.operatingsystem = [self.operatingsystem]
        self.ptable.operatingsystem = [self.operatingsystem]

    class Meta:
        api_class = HostApi
