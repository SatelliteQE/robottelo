"""
Usage::

    hammer location [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add-compute-resource          Associate a compute resource
    add-domain                    Associate a domain
    add-environment               Associate an environment
    add-hostgroup                 Associate a hostgroup
    add-medium                    Associate a medium
    add-organization              Associate an organization
    add-provisioning-template     Associate provisioning templates
    add-smart-proxy               Associate a smart proxy
    add-subnet                    Associate a subnet
    add-user                      Associate an user
    create                        Create a location
    delete                        Delete a location
    info                          Show a location
    list                          List all locations
    remove-compute-resource       Disassociate a compute resource
    remove-domain                 Disassociate a domain
    remove-environment            Disassociate an environment
    remove-hostgroup              Disassociate a hostgroup
    remove-medium                 Disassociate a medium
    remove-organization           Disassociate an organization
    remove-provisioning-template  Disassociate provisioning templates
    remove-smart-proxy            Disassociate a smart proxy
    remove-subnet                 Disassociate a subnet
    remove-user                   Disassociate an user
    update                        Update a location
"""

from robottelo.cli.base import Base


class Location(Base):
    """Manipulates Foreman's Locations"""

    command_base = 'location'

    @classmethod
    def add_compute_resource(cls, options=None):
        """Associate a compute resource"""

        cls.command_sub = 'add-compute-resource'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_domain(cls, options=None):
        """Associate a domain"""

        cls.command_sub = 'add-domain'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_environment(cls, options=None):
        """Associate an environment"""

        cls.command_sub = 'add-environment'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_hostgroup(cls, options=None):
        """Associate a hostgroup"""

        cls.command_sub = 'add-hostgroup'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_medium(cls, options=None):
        """Associate a medium"""

        cls.command_sub = 'add-medium'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_organization(cls, options=None):
        """Associate an organization"""

        cls.command_sub = 'add-organization'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_provisioning_template(cls, options=None):
        """Associate a provisioning template"""

        cls.command_sub = 'add-provisioning-template'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_smart_proxy(cls, options=None):
        """Associate a smart proxy"""

        cls.command_sub = 'add-smart-proxy'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_subnet(cls, options=None):
        """Associate a subnet"""

        cls.command_sub = 'add-subnet'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_user(cls, options=None):
        """Associate a user"""

        cls.command_sub = 'add-user'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_compute_resource(cls, options=None):
        """Disassociate a compute resource"""

        cls.command_sub = 'remove-compute-resource'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_domain(cls, options=None):
        """Disassociate a domain"""

        cls.command_sub = 'remove-domain'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_environment(cls, options=None):
        """Disassociate an environment"""

        cls.command_sub = 'remove-environment'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_hostgroup(cls, options=None):
        """Disassociate a hostgroup"""

        cls.command_sub = 'remove-hostgroup'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_medium(cls, options=None):
        """Disassociate a medium"""

        cls.command_sub = 'remove-medium'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_organization(cls, options=None):
        """Disassociate an organization"""

        cls.command_sub = 'remove-organization'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_provisioning_template(cls, options=None):
        """Disassociate a provisioning template"""

        cls.command_sub = 'remove-provisioning-template'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_smart_proxy(cls, options=None):
        """Disassociate a smart proxy"""

        cls.command_sub = 'remove-smart-proxy'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_subnet(cls, options=None):
        """Disassociate a subnet"""

        cls.command_sub = 'remove-subnet'

        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_user(cls, options=None):
        """Disassociate a user"""

        cls.command_sub = 'remove-user'

        return cls.execute(cls._construct_command(options))
