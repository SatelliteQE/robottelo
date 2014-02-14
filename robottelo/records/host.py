from robottelo.api.hosts import HostApi
from robottelo.common import records
from robottelo.records.architecture import Architecture
from robottelo.records.domain import Domain
from robottelo.records.environment import Environment
from robottelo.records.operatingsystem import OperatingSystem
from robottelo.records.partitiontable import PartitionTable
from robottelo.records.smartproxy import SmartProxy


class Host(records.Record):
    name = records.StringField(format=r"host\d\d\d\d\d")
    root_pass = records.StringField("changeme")
    mac = records.MACField()
    environment = records.RelatedField(Environment)
    architecture = records.RelatedField(Architecture)
    domain = records.RelatedField(Domain)
    puppet_proxy = records.RelatedField(SmartProxy)
    operatingsystem = records.RelatedField(OperatingSystem)
    ptable = records.RelatedField(PartitionTable)

    def _post_init(self):
        self.name = self.name + "." + self.domain.name
        self.architecture.operatingsystem = [self.operatingsystem]
        self.ptable.operatingsystem = [self.operatingsystem]

    class Meta:
        api_class = HostApi
