from robottelo.api.architectures import ArchitectureApi
from robottelo.common import records


class Architectures(records.Record):
    name = records.StringField(required=True)

    class Meta:
        api_class = ArchitectureApi
