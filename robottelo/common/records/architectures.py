from robottelo.common import records
from robottelo.api.architectures import ArchitectureApi

class Architectures(records.Record):
    name = records.StringField(required=True)

    class Meta:
        api_class = ArchitectureApi
