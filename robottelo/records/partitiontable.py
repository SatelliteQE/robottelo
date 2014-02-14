from robottelo.api.ptables import PTableApi
from robottelo.common import records
from robottelo.common.constants import OPERATING_SYSTEMS
from robottelo.records.operatingsystem import OperatingSystem


class PartitionTable(records.Record):
    name = records.StringField()
    layout = records.StringField(default="d-i partman-auto/disk")
    operatingsystem = records.ManyRelatedField(OperatingSystem, 1, 3)
    os_family = records.ChoiceField(OPERATING_SYSTEMS)

    class Meta:
        api_class = PTableApi
