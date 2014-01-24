from robottelo.common import records
from robottelo.api.domains import DomainApi
from robottelo.cli.records.domains import DomainCli

class Domains(records.Record):
    name = records.StringField(format=r"(?!-)[a-z\d-]{1,63}(?<!-)$",required=True)

    class Meta:
        api_class = DomainApi
        cli_class = DomainCli
