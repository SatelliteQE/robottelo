from robottelo.common import records
from robottelo.api.domains import DomainApi

class Domains(records.Record):
    name = records.StringField(required=True)

    class Meta:
        api_class = DomainApi
