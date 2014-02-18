from robottelo.common import records
from robottelo.common.constants import OPERATING_SYSTEMS
from robottelo.records.operatingsystem import OperatingSystem
from robottelo.api.apicrud import ApiCrud


class PTableApi(ApiCrud):
        api_path = "/api/ptables/"
        api_json_key = u"ptable"

        create_fields = ["name",
                         "layout",
                         "operatingsystem_ids",
                         "os_family"]

class PartitionTable(records.Record):
    name = records.StringField()
    layout = records.StringField(default="d-i partman-auto/disk")
    operatingsystem = records.ManyRelatedField(OperatingSystem, 1, 3)
    os_family = records.ChoiceField(OPERATING_SYSTEMS)

    class Meta:
        api_class = PTableApi
