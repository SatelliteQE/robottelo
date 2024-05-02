"""
Usage::

    hammer auth-source ldap [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::
    create                        Create an LDAP authentication source
    delete                        Delete an LDAP authentication source
    info                          Show an LDAP authentication source
    list                          List all LDAP authentication sources
    update                        Update an LDAP authentication source
"""

from robottelo.cli.base import Base


class LDAPAuthSource(Base):
    """Manipulates LDAP auth source"""

    command_base = 'auth-source ldap'


class ExternalAuthSource(Base):
    """Manipulates External auth source

    Usage:
        hammer auth-source external [OPTIONS] SUBCOMMAND [ARG] ...

    Subcommands:
        info           Show an external user group for user group
        list           List all external user groups for user group
        update         Update external user group
    """

    command_base = 'auth-source external'
