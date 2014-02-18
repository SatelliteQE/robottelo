from robottelo.common import records
from robottelo.records import Architecture
from robottelo.records import Domain
from robottelo.records import Environment
from robottelo.records import OperatingSystem
from robottelo.records import PartitionTable
from robottelo.records import SmartProxy
from robottelo.api.apicrud import ApiCrud

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
    root_pass = records.StringField(default = "changeme")
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
