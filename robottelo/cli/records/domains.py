from robottelo.cli.domain import Domain
from robottelo.cli.records.clicrud import CliCrud

class DomainCli(CliCrud):

        cli_object = Domain()
        create_fields = ["name", "dns_id", "description"]


