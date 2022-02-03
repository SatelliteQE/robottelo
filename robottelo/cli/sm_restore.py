"""
Usage:
    satellite-maintain restore [OPTIONS] BACKUP_DIR

Parameters:
    BACKUP_DIR                    Path to backup directory to restore

Options:
    -y, --assumeyes               Automatically answer yes for all questions
    -w, --whitelist whitelist     Comma-separated list of labels of steps to be skipped
    -f, --force                   Force steps that would be skipped as they were already run
    -i, --incremental             Restore an incremental backup
    -h, --help                    print help
"""
from robottelo.cli.base import Base


class Restore(Base):
    """Manipulates Satellite-maintain's restore command"""

    command_base = 'restore'

    @classmethod
    def run(cls, backup_dir='/tmp/', timeout='30m', options=None):
        """Build satellite-maintain restore"""
        # cls.command_sub = 'No subcommand for restore'
        cls.command_end = backup_dir
        options = options or {}
        return cls.sm_execute(cls._construct_command(options), timeout=timeout)
