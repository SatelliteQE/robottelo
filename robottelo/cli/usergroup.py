"""
Usage::
    hammer user-group [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::
    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::
    add-role                      Assign a user role
    add-user                      Associate an user
    add-user-group                Associate an user group
    create                        Create a user group
    delete                        Delete a user group
    external                      View and manage external user groups
    info                          Show a user group
    list                          List all user groups
    remove-role                   Remove a user role
    remove-user                   Disassociate an user
    remove-user-group             Disassociate an user group
    update                        Update a user group
"""

from robottelo.cli.base import Base


class UserGroup(Base):
    """Manipulates Foreman's user group."""

    command_base = 'user-group'

    @classmethod
    def add_role(cls, options=None):
        """Assign a user role.

        Usage:
            hammer user-group add-role [OPTIONS]

        Options:
            --id ID
            --name NAME                   Name to search by
            --role ROLE_NAME              User role name
            --role-id ROLE_ID
        """
        cls.command_sub = 'add-role'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def add_user(cls, options=None):
        """Associate an user.

        Usage:
            hammer user-group add-user [OPTIONS]

        Options:
            --id ID
            --name NAME                   Name to search by
            --user USER_LOGIN             User's login to search by
            --user-id USER_ID
        """
        cls.command_sub = 'add-user'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def add_user_group(cls, options=None):
        """Associate an user group.

        Usage:
            hammer user-group add-user-group [OPTIONS]

        Options:
            --id ID
            --name NAME                                   Name to search by
            --user-group USER_GROUP_NAME                  Name to search by
            --user-group-id USER_GROUP_ID
        """
        cls.command_sub = 'add-user-group'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def remove_role(cls, options=None):
        """Remove a user role.

        Usage:
            hammer user-group remove-role [OPTIONS]

        Options:
            --id ID
            --name NAME                   Name to search by
            --role ROLE_NAME              User role name
            --role-id ROLE_ID
        """
        cls.command_sub = 'remove-role'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def remove_user(cls, options=None):
        """Disassociate an user.

        Usage:
            hammer user-group remove-user [OPTIONS]

        Options:
            --id ID
            --name NAME                   Name to search by
            --user USER_LOGIN             User's login to search by
            --user-id USER_ID
        """
        cls.command_sub = 'remove-user'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def remove_user_group(cls, options=None):
        """Disassociate an user group.

        Usage:
            hammer user-group remove-user-group [OPTIONS]

        Options:
            --id ID
            --name NAME                                   Name to search by
            --user-group USER_GROUP_NAME                  Name to search by
            --user-group-id USER_GROUP_ID
        """
        cls.command_sub = 'remove-user-group'
        return cls.execute(cls._construct_command(options), output_format='csv')


class UserGroupExternal(Base):
    """Manages Foreman external user groups.

    Usage:
        hammer user-group external [OPTIONS] SUBCOMMAND [ARG] ...

    Subcommands:
        create         Create an external user group linked to a user group
        delete         Delete an external user group
        info           Show an external user group for user group
        list           List all external user groups for user group
        refresh        Refresh external user group
        update         Update external user group
    """

    command_base = 'user-group external'

    @classmethod
    def refresh(cls, options=None):
        cls.command_sub = 'refresh'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def create(cls, options=None, timeout=None):
        """Create external user group"""
        cls.command_sub = 'create'
        result = cls.execute(cls._construct_command(options), output_format='csv', timeout=timeout)
        # External user group can only be fetched by specifying both id and
        # user group id it is linked to
        if len(result) > 0 and 'id' in result[0]:
            info_options = {'user-group-id': options.get('user-group-id'), 'id': result[0]['id']}
            result = cls.info(info_options)
        return result
