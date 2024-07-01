"""
Usage::

    hammer organization [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add-computeresource           Associate a resource
    add-domain                    Associate a resource
    add-environment               Associate a resource
    add-hostgroup                 Associate a resource
    add-location                  Associate a location
    add-medium                    Associate a resource
    add-provisioning-template     Associate provisioning templates
    add-smartproxy                Associate a resource
    add-subnet                    Associate a resource
    add-user                      Associate a resource
    create                        Create an organization
    configure-cdn                 Update the CDN configuration
    delete                        Delete an organization
    delete-parameter              Delete parameter for an organization.
    info                          Show an organization
    list                          List all organizations
    remove_computeresource        Disassociate a resource
    remove_domain                 Disassociate a resource
    remove_environment            Disassociate a resource
    remove_hostgroup              Disassociate a resource
    remove-location               Disassociate a location
    remove_medium                 Disassociate a resource
    remove-provisioning-template  Disassociate provisioning templates
    remove_smartproxy             Disassociate a resource
    remove_subnet                 Disassociate a resource
    remove_user                   Disassociate a resource
    set-parameter                 Create or update parameter for an
                                    organization.
    update                        Update an organization
"""

from robottelo.cli.base import Base


class Org(Base):
    """Manipulates Foreman's Organizations"""

    command_base = 'organization'

    @classmethod
    def add_compute_resource(cls, options=None):
        """Adds a computeresource to an org"""
        cls.command_sub = 'add-compute-resource'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_compute_resource(cls, options=None):
        """Removes a computeresource from an org"""
        cls.command_sub = 'remove-compute-resource'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_domain(cls, options=None):
        """Adds a domain to an org"""
        cls.command_sub = 'add-domain'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_domain(cls, options=None):
        """Removes a domain from an org"""
        cls.command_sub = 'remove-domain'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_environment(cls, options=None):
        """Adds an environment to an org"""
        cls.command_sub = 'add-environment'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_environment(cls, options=None):
        """Removes an environment from an org"""
        cls.command_sub = 'remove-environment'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_hostgroup(cls, options=None):
        """Adds a hostgroup to an org"""
        cls.command_sub = 'add-hostgroup'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_hostgroup(cls, options=None):
        """Removes a hostgroup from an org"""
        cls.command_sub = 'remove-hostgroup'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_location(cls, options=None):
        """Adds a location to an org"""
        cls.command_sub = 'add-location'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_location(cls, options=None):
        """Removes a location from an org"""
        cls.command_sub = 'remove-location'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_medium(cls, options=None):
        """Adds a medium to an org"""
        cls.command_sub = 'add-medium'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_medium(cls, options=None):
        """Removes a medium from an org"""
        cls.command_sub = 'remove-medium'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_provisioning_template(cls, options=None):
        """Adds a provisioning template to an org"""
        cls.command_sub = 'add-provisioning-template'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_provisioning_template(cls, options=None):
        """Removes a provisioning template from an org"""
        cls.command_sub = 'remove-provisioning-template'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_smart_proxy(cls, options=None):
        """Adds a smartproxy to an org"""
        cls.command_sub = 'add-smart-proxy'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_smart_proxy(cls, options=None):
        """Removes a smartproxy from an org"""
        cls.command_sub = 'remove-smart-proxy'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_subnet(cls, options=None):
        """Adds existing subnet to an org"""
        cls.command_sub = 'add-subnet'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_subnet(cls, options=None):
        """Removes a subnet from an org"""
        cls.command_sub = 'remove-subnet'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def add_user(cls, options=None):
        """Adds an user to an org"""
        cls.command_sub = 'add-user'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def remove_user(cls, options=None):
        """Removes an user from an org"""
        cls.command_sub = 'remove-user'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def configure_cdn(cls, options=None):
        """Update the CDN configuration"""
        cls.command_sub = 'configure-cdn'
        return cls.execute(cls._construct_command(options))
