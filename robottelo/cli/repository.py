"""
Usage::

    hammer repository [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    create                        Create a repository
    delete                        Destroy a repository
    info                          Show a repository
    list                          List of repositories
    remove-content                Remove content from the repository
    synchronize                   Sync a repository
    update                        Update a repository
    upload-content                Upload content into the repository
"""
from robottelo.cli.base import Base


class Repository(Base):
    """
    Manipulates Katello engine's repository command.
    """

    command_base = 'repository'
    command_requires_org = True

    @classmethod
    def create(cls, options=None):
        """Create a custom repository"""
        cls.command_requires_org = False

        try:
            result = super().create(options)
        finally:
            cls.command_requires_org = True

        return result

    @classmethod
    def info(cls, options=None):
        """Show a custom repository"""
        cls.command_requires_org = False

        try:
            result = super().info(options)
        finally:
            cls.command_requires_org = True

        return result

    @classmethod
    def synchronize(cls, options, return_raw_response=None, timeout=3600):
        """Synchronizes a repository."""
        cls.command_sub = 'synchronize'
        return cls.execute(
            cls._construct_command(options),
            output_format='csv',
            ignore_stderr=True,
            return_raw_response=return_raw_response,
            timeout=timeout,
        )

    @classmethod
    def remove_content(cls, options):
        """Remove content from a repository"""
        cls.command_sub = 'remove-content'
        return cls.execute(cls._construct_command(options), output_format='csv', ignore_stderr=True)

    @classmethod
    def upload_content(cls, options):
        """Upload content to repository."""
        cls.command_sub = 'upload-content'
        return cls.execute(cls._construct_command(options), output_format='csv', ignore_stderr=True)
