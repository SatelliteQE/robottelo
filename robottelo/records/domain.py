from robottelo.api.domains import DomainApi
from robottelo.common import records


class Domain(records.Record):
    name = records.StringField(format=r"domain\d\d\d\d")

    class Meta:
        api_class = DomainApi

