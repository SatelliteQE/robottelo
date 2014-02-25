# -*- encoding: utf-8 -*-

"""
Module for Host api an record implementation
"""


from robottelo.common import records
from robottelo.api.apicrud import ApiCrud
from robottelo.records.environment import Environment
from robottelo.records.architecture import Architecture
from robottelo.records.domain import Domain
from robottelo.records.smartproxy import SmartProxy
from robottelo.records.partitiontable import PartitionTable
from robottelo.records.operatingsystem import OperatingSystem


class HostApi(ApiCrud):
    """ Implementation of api for  foreman hosts
    """
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
    """ Implementation of foreman hosts record
    Utilizes _post_init to ensure, that name matches domain,
    operating system matches architecture and partition table
    """
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
        """Ensures, that certain fields are consistent
        with api requirements
        """
        self.name = self.name + "." + self.domain.name
        self.architecture.operatingsystem = [self.operatingsystem]
        self.ptable.operatingsystem = [self.operatingsystem]

    class Meta:
        """Linking record definition with api implementation.
        """
        api_class = HostApi
