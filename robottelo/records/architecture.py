from robottelo.common import records
from robottelo.records.operatingsystem import OperatingSystem


class Architecture(records.Record):
    name = records.StringField(required=True)
    operatingsystem = records.ManyRelatedField(OperatingSystem, 1, 3)
