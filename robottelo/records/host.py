from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.records.environment import Environment
from robottelo.records.architecture import Architecture
from robottelo.records.domain import Domain
from robottelo.records.smartproxy import SmartProxy
from robottelo.records.partitiontable import PartitionTable
from robottelo.records.operatingsystem import OperatingSystem


class HostApi(ApiCrud):
        api_path = "/api/hosts/"
        api_json_key = u"host"
        create_fields = ["name",
                         "environment_id",
                         "architecture_id",
                         "root_pass",
                         "mac",
                         "domain_id",
                         "puppet_proxy_id",
                         "ptable_id",
                         "operatingsystem_id"]


class Host(records.Record):
    name = records.StringField(format=r"host\d\d\d\d\d")
    root_pass = records.StringField(default="changeme")
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
