from robottelo.api.apicrud import ApiCrud
from robottelo.common import records
from robottelo.records.operatingsystem import OperatingSystem


class ArchitectureApi(ApiCrud):
    """Implementation of Architecture api"""
    api_path = "/api/architectures/"
    api_json_key = u"architecture"
    create_fields = ["name", "operatingsystem_ids"]


class Architecture(records.Record):
    """Definition of architecture entity"""
    name = records.StringField(required=True)
    operatingsystem = records.ManyRelatedField(OperatingSystem, 1, 3)

    class Meta:
        api_class = ArchitectureApi
