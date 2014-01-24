from robottelo.api.domains import DomainApi
from robottelo.common import records
from robottelo.cli.records.domains import DomainCli

class Domains(records.Record):
    name = records.StringField(format="domain\d\d\d\d",required=True)

    class Meta:
        api_class = DomainApi
        cli_class = DomainCli
