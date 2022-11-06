"""
Usage:
    satellite-maintain upgrade [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    list-versions                 List versions this system is upgradable to
    check                         Run pre-upgrade checks before upgrading to specified version
    run                           Run full upgrade to a specified version

Options:
    -h, --help                    print help
"""
from robottelo.cli.base import Base


class Upgrade(Base):
    """Manipulates Satellite-maintain's health command"""

    command_base = 'upgrade'

    @classmethod
    def list_versions(cls, options=None, env_var=None):
        """Build satellite-maintain upgrade list-versions"""
        cls.command_sub = 'list-versions'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def check(cls, options=None, env_var=None):
        """Build satellite-maintain upgrade check"""
        cls.command_sub = 'check'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)

    @classmethod
    def run(cls, options=None, env_var=None):
        """Build satellite-maintain upgrade run"""
        cls.command_sub = 'run'
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), env_var=env_var)
