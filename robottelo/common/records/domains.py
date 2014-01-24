from robottelo.api.domains import DomainApi
from robottelo.common import records


class Domains(records.Record):
    name = records.StringField(required=True)

    class Meta:
        api_class = DomainApi
