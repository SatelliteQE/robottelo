"""
Usage::

    hammer user [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    access-token                  Managing personal access tokens
    add-role                      Assign a user role
    create                        Create an user.
    delete                        Delete an user.
    info                          Show an user.
    list                          List all users.
    remove-role                   Remove a user role
    ssh-keys                      Managing User SSH Keys.
    update                        Update an user.
"""

from robottelo.cli.base import Base


class User(Base):
    """
    Manipulates Foreman's users.
    """

    command_base = 'user'

    @classmethod
    def add_role(cls, options=None):
        """Add a role to a user."""
        cls.command_sub = 'add-role'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def remove_role(cls, options=None):
        """Remove a role from user."""
        cls.command_sub = 'remove-role'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def ssh_keys_add(cls, options=None):
        """
        Usage:
        hammer user ssh-keys add [OPTIONS]

        Options:
        --key KEY                               Public SSH key
        --key-file KEY_FILE                     Path to a SSH public key
        --location LOCATION_NAME                Location name
        --location-id LOCATION_ID
        --location-title LOCATION_TITLE         Location title
        --name NAME
        --organization ORGANIZATION_NAME        Organization name
        --organization-id ORGANIZATION_ID       Organization ID
        --organization-title ORGANIZATION_TITLE Organization title
        --user USER_LOGIN                       User's login to search by
        --user-id USER_ID

        """
        cls.command_sub = 'ssh-keys add'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def ssh_keys_delete(cls, options=None):
        """
        Usage:
        hammer user ssh-keys delete [OPTIONS]

        """
        cls.command_sub = 'ssh-keys delete'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def ssh_keys_list(cls, options=None):
        """
        Usage:
        hammer user ssh-keys list [OPTIONS]

        """
        cls.command_sub = 'ssh-keys list'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def ssh_keys_info(cls, options=None):
        """
        Usage:
        hammer user ssh-keys info [OPTIONS]

        """
        cls.command_sub = 'ssh-keys info'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def access_token(cls, action=None, options=None):
        """
        Usage:
        hammer user access-token [ARG] ...

        action: create | revoke
        """
        cls.command_sub = f'access-token {action}'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def mail_notification_add(cls, options=None):
        """
        Usage:
        hammer user mail-notification add [OPTIONS]

        Options::

            --interval VALUE                        Mail notification interval option, e.g. Daily,
                                                    Weekly or Monthly.
                                                    Required for summary notification
            --location[-id|-title] VALUE/NUMBER     Set the current location context for the request
            --mail-notification[-id] VALUE/NUMBER
            --mail-query VALUE                      Relevant only for audit summary notification
            --organization[-id|-title] VALUE/NUMBER Set the current organization context
                                                    for the request
            --subscription VALUE                    Mail notification subscription option, e.g.
                                                    Subscribe, Subscribe to my hosts or
                                                    Subscribe to all hosts. Required for host built
                                                    and config error state
            --user[-id] VALUE

        """
        cls.command_sub = 'mail-notification add'
        return cls.execute(cls._construct_command(options), output_format='csv')
