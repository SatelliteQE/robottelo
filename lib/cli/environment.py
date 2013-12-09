"""
Usage:
    hammer environment [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    create                        Create an environment.
    info                          Show an environment.
    list                          List all environments.
    update                        Update an environment.
    sc_params                     List all smart class parameters
    delete                        Delete an environment.
"""
from lib.cli.base import Base


class Environment(Base):

    OUT_ENV_CREATED = "Environment created"
    OUT_ENV_UPDATED = "Environment updated"
    OUT_ENV_DELETED = "Environment deleted"

    def __init__(self):
        self.command_base = "environment"
