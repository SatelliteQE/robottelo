from robottelo.api.architectures import ArchitectureApi
from robottelo.common import records
from robottelo.records.operatingsystem import OperatingSystem


class Architecture(records.Record):
    name = records.StringField(required=True)
    operatingsystem = records.ManyRelatedField(OperatingSystem, 1, 3)

    class Meta:
        api_class = ArchitectureApi

