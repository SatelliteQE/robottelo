"""
Usage:
    foreman-maintain upgrade [OPTIONS] SUBCOMMAND [ARG] ...

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
    """Manipulates Foreman-maintain's health command"""

    command_base = "upgrade"

    @classmethod
    def list_versions(cls, options=None):
        """Build foreman-maintain upgrade list-versions"""
        cls.command_sub = "list-versions"
        if options is None:
            options = {}
        return cls.fm_execute(cls._construct_command(options))

    @classmethod
    def check(cls, options=None):
        """Build foreman-maintain upgrade check"""
        cls.command_sub = "check"
        if options is None:
            options = {}
        return cls.fm_execute(cls._construct_command(options))

    @classmethod
    def run(cls, options=None):
        """Build foreman-maintain upgrade run"""
        cls.command_sub = "run"
        if options is None:
            options = {}
        return cls.fm_execute(cls._construct_command(options))
