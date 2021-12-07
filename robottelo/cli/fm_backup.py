"""
Usage:
    foreman-maintain backup [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands:
    online                        Keep services online during backup
    offline                       Shut down services to preserve consistent backup
    snapshot                      Use snapshots of the databases to create backup

Options:
    -h, --help                    print help
"""
from robottelo.cli.base import Base


class Backup(Base):
    """Manipulates Foreman-maintain's backup command"""

    command_base = "backup"

    @classmethod
    def run_backup(cls, options=None, backup_dir='/tmp/', backup_type='online', timeout=None):
        """Build foreman-maintain backup online/offline/snapshot"""
        cls.command_sub = backup_type
        cls.command_end = backup_dir
        if options is None:
            options = {}
        return cls.fm_execute(cls._construct_command(options), timeout=timeout)
