"""
Usage::
    hammer host [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::
    SUBCOMMAND                    Subcommand
    [ARG] ...                     Subcommand arguments

Subcommands::
     ansible-roles                 Manage Ansible roles on a host
     boot                          Boot host from specified device
     config-reports                List all reports
     create                        Create a host
     deb-package                   Manage deb packages on your hosts
     delete                        Delete a host
     delete-parameter              Delete parameter for a host
     disassociate                  Disassociate a host
     enc-dump                      Dump host's ENC YAML
     errata                        Manage errata on your hosts
     facts                         List all fact values
     info                          Show a host
     interface                     View and manage host's network interfaces
     list                          List all hosts
     package                       Manage packages on your hosts
     package-group                 Manage package-groups on your hosts
     policies-enc                  View policies ENC for host
     puppet-classes                List all Puppet classes
     reboot                        Reboot a host
     rebuild-config                Rebuild orchestration related configurations for host
     reports                       List all reports
     reset                         Reset a host
     sc-params                     List all smart class parameters
     set-parameter                 Create or append a parameter for a host
     start                         Power a host on
     status                        Get status of host
     stop                          Power a host off
     subscription                  Manage subscription information on your hosts
     traces                        List traces on your hosts
     update                        Update a host

"""
from robottelo.cli.base import Base


class Host(Base):
    """Manipulates Foreman's hosts."""

    command_base = 'host'

    @classmethod
    def ansible_roles_play(cls, options):
        """Plays the associated ansible-roles"""
        cls.command_sub = 'ansible-roles play'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def disassociate(cls, options):
        """Disassociate the host from a CR."""
        cls.command_sub = 'disassociate'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def enc_dump(cls, options):
        """
        Dump host's ENC YAML.

        Usage::

            hammer host enc-dump [OPTIONS]

        Options::

             --id ID
             --location LOCATION_NAME                Location name
             --location-id LOCATION_ID
             --location-title LOCATION_TITLE         Location title
             --name NAME                             Host name
             --organization ORGANIZATION_NAME        Organization name
             --organization-id ORGANIZATION_ID       Organization ID
             --organization-title ORGANIZATION_TITLE Organization title
             -h, --help                              Print help
        """
        cls.command_sub = 'enc-dump'
        return cls.execute(cls._construct_command(options), output_format='yaml')

    @classmethod
    def errata_apply(cls, options):
        """Schedule errata for installation"""
        cls.command_sub = 'errata apply'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def errata_info(cls, options):
        """Retrieve a single errata for a system"""
        cls.command_sub = 'errata info'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def errata_list(cls, options):
        """List errata available for the content host."""
        cls.command_sub = 'errata list'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def facts(cls, options=None):
        """
        List all fact values.

        Usage::

            hammer host facts [OPTIONS]

        Options::

            --id ID                       resource id
            --name NAME                   resource name
            --order ORDER                 sort results
            --page PAGE                   paginate results
            --per-page PER_PAGE           number of entries per request
            --search SEARCH               filter results
            -h, --help                    print help
        """
        cls.command_sub = 'facts'

        result = cls.execute(cls._construct_command(options), output_format='csv')

        facts = []

        if result:
            facts = result

        return facts

    @classmethod
    def package_install(cls, options):
        """Install packages remotely."""
        cls.command_sub = 'package install'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def package_list(cls, options):
        """List packages installed on the host."""
        cls.command_sub = 'package list'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def package_remove(cls, options):
        """Uninstall packages remotely."""
        cls.command_sub = 'package remove'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def package_upgrade(cls, options):
        """Update packages remotely."""
        cls.command_sub = 'package upgrade'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def package_upgrade_all(cls, options):
        """Update all packages remotely."""
        cls.command_sub = 'package upgrade-all'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def package_group_install(cls, options):
        """Install package groups remotely."""
        cls.command_sub = 'package-group install'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def package_group_remove(cls, options):
        """Uninstall package groups remotely."""
        cls.command_sub = 'package-group remove'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def reboot(cls, options=None):
        """
        Reboot a host

        Usage::

            hammer host reboot [OPTIONS]

        Options::

            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        cls.command_sub = 'reboot'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def reports(cls, options=None):
        """
        List all reports.

        Usage::

            hammer host reports [OPTIONS]

        Options::

            --id ID                       resource id
            --name NAME                   resource name
            --order ORDER                 sort results
            --page PAGE                   paginate results
            --per-page PER_PAGE           number of entries per request
            --search SEARCH               filter results
            -h, --help                    print help
        """

        cls.command_sub = 'reports'

        result = cls.execute(cls._construct_command(options), output_format='csv')

        reports = []

        if result:
            reports = result

        return reports

    @classmethod
    def start(cls, options=None):
        """
        Power a host on

        Usage::

            hammer host start [OPTIONS]

        Options::

            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        cls.command_sub = 'start'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def status(cls, options=None):
        """
        Get status of host

        Usage::

            hammer host status [OPTIONS]

        Options::

            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        cls.command_sub = 'status'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def stop(cls, options=None):
        """
        Power a host off

        Usage::

            hammer host stop [OPTIONS]

        Options::

            --force                       Force turning off a host
            --id ID                       resource id
            --name NAME                   resource name
            -h, --help                    print help
        """

        cls.command_sub = 'stop'

        result = cls.execute(cls._construct_command(options))

        return result

    @classmethod
    def subscription_register(cls, options=None):
        """Register a host with subscription and information.

        Usage::

            hammer host subscription register [OPTIONS]

        Options::

            --content-view CONTENT_VIEW_NAME                    Content view
                                                                name to search
                                                                by
            --content-view-id CONTENT_VIEW_ID                   content view
                                                                numeric
                                                                identifier
            --hypervisor-guest-uuids HYPERVISOR_GUEST_UUIDS     UUIDs of the
                                                                virtual guests
                                                                from the
                                                                host&#39;s
                                                                hypervisor
                                                                Comma separated
                                                                list of values.
            --lifecycle-environment LIFECYCLE_ENVIRONMENT_NAME  Lifecycle
                                                                environment
                                                                name to search
                                                                by
            --lifecycle-environment-id LIFECYCLE_ENVIRONMENT_ID  ID of the
                                                                 environment
            --name NAME                                         Name of the
                                                                host
            --organization ORGANIZATION_NAME                    Organization
                                                                name to search
                                                                by
            --organization-id ORGANIZATION_ID                   organization ID
            --organization-label ORGANIZATION_LABEL             Organization
                                                                label to search
                                                                by
            --release-version RELEASE_VERSION                   Release version
                                                                of the content
                                                                host
            --service-level SERVICE_LEVEL                       A service level
                                                                for
                                                                auto-healing
                                                                process, e.g.
                                                                SELF-SUPPORT
            --uuid UUID                                         UUID to use for
                                                                registered
                                                                host, random
                                                                uuid is
                                                                generated if
                                                                not provided
        """
        cls.command_sub = 'subscription register'
        result = cls.execute(cls._construct_command(options), output_format='csv')
        if isinstance(result, list):
            result = result[0]
        return result

    @classmethod
    def subscription_unregister(cls, options=None):
        """Unregister the host as a subscription consumer.

        Usage::

            hammer host subscription unregister [OPTIONS]

        Options::

            --host HOST_NAME              Name to search by
            --host-id HOST_ID             Host ID
        """
        cls.command_sub = 'subscription unregister'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def subscription_attach(cls, options=None):
        """Attach a subscription to host

        Usage::

            hammer host subscription attach [OPTIONS]

        Options::

            --host HOST_NAME                  Name to search by
            --host-id HOST_ID                 Host ID
            --quantity Quantity               Quantity of this subscriptions to
                                              add. Defaults to 1
            --subscription-id SUBSCRIPTION_ID ID of subscription
        """
        cls.command_sub = 'subscription attach'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def subscription_remove(cls, options=None):
        """Remove a subscription from host

        Usage::

            hammer host subscription remove [OPTIONS]

        Options::

            --host HOST_NAME                    Name to search by
            --host-id HOST_ID
            --quantity Quantity                 Remove the first instance of a
                                                subscription with matching id
                                                and quantity
            --subscription-id SUBSCRIPTION_ID   ID of subscription
        """
        cls.command_sub = 'subscription remove'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def subscription_auto_attach(cls, options=None):
        """Auto attach subscription to host

        Usage::

            hammer host subscription auto-attach [OPTIONS]

        Options::

            --host HOST_NAME              Name to search by
            --host-id HOST_ID
            -h, --help                    print help
        """
        cls.command_sub = 'subscription auto-attach'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def sc_params(cls, options=None):
        """List all smart class parameters

        Usage::

            hammer host sc-params [OPTIONS]

        Options::

            --host HOST_NAME              Host name
            --host-id HOST_ID
            --order ORDER                 sort results
            --page PAGE                   paginate results
            --per-page PER_PAGE           number of entries per request
            --search SEARCH               filter results
        """
        cls.command_sub = 'sc-params'
        return cls.execute(cls._construct_command(options), output_format='csv')


class HostInterface(Base):
    """Manages interface functionality for hosts.

    Usage::
        hammer host interface [OPTIONS] SUBCOMMAND [ARG] ...

    Subcommands::
        create         Create an interface on a host
        delete         Delete a host's interface
        info           Show an interface for host
        list           List all interfaces for host
        update         Update a host's interface
    """

    command_base = 'host interface'

    @classmethod
    def create(cls, options=None):
        """Create new network interface for host"""
        cls.command_sub = 'create'
        cls.execute(cls._construct_command(options), output_format='csv')


class HostTraces(Base):
    """Manages traces on your hosts

    Usage::
        hammer host traces [OPTIONS] SUBCOMMAND [ARG] ...

    Subcommands::
        list                          List services that need restarting on the host
        resolve                       Resolve Traces
    """

    command_base = 'host traces'

    @classmethod
    def list(cls, options=None):
        """List services that need restarting on the host.

        Usage::

            hammer host traces list [OPTIONS]

        Options::

            --fields FIELDS               Show specified fields or predefined field sets only.
                                        (See below) Comma separated list of values.
                                        Values containing comma should be quoted or
                                        escaped with backslash.
                                       JSON is acceptable and preferred way for complex parameters
            --host[-id]                   Name/id of the host
        """
        cls.command_sub = 'list'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def resolve(cls, options=None):
        """Resolve Traces

        Usage::

            hammer host traces resolve [OPTIONS]

        Options::

            --async                       Do not wait for the task
            --host[-id]                   Name/id of the host
            --trace-ids TRACE_IDS         Array of Trace ids
                                       Comma separated list of values.
                                       Values containing comma should be quoted or
                                       escaped with backslash.
                                       JSON is acceptable and preferred way for complex parameters
        """
        cls.command_sub = 'resolve'
        cls.execute(cls._construct_command(options))
