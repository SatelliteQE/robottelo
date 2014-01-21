from robottelo.common import records
from robottelo.api.architectures import ArchitectureApi
from robottelo.common.records.operatingsystems import OperatingSystems

class Architectures(records.Record):
    name = records.StringField(required=True)
    operatingsystem = records.ManyRelatedFields(OperatingSystems,1,3)

    class Meta:
        api_class = ArchitectureApi
