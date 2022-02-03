"""
Usage:
    satellite-maintain backup [OPTIONS] SUBCOMMAND [ARG] ...

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
    """Manipulates Satellite-maintain's backup command"""

    command_base = 'backup'

    @classmethod
    def run_backup(cls, backup_dir='/tmp/', backup_type='online', options=None, timeout=None):
        """Build satellite-maintain backup online/offline/snapshot"""
        cls.command_sub = backup_type
        cls.command_end = backup_dir
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), timeout=timeout)
