# -*- encoding: utf-8 -*-
"""
Usage:
    hammer csv [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    subcommand
 [ARG] ...                     subcommand arguments

Subcommands:
 activation-keys               import or export activation keys
 content-hosts                 import or export content hosts
 export                        export into directory
 import                        import by directory
 settings                      import or export settings
 subscriptions                 import or export subscriptions

Options:
 -h, --help                    print help
"""
from robottelo.cli.base import Base


class CSV_(Base):
    """Manipulates csv  import/export operations"""

    command_base = 'csv'

    @classmethod
    def activation_keys(cls, options=None):
        """Import or export activation keys

        hammer csv activation-keys --help

        Usage::

            hammer csv activation-keys [OPTIONS]

        Options::

            --continue-on-error           Continue processing even if
                                          individual resource error
            --export                      Export current data instead of
                                          importing
            --file FILE_NAME              CSV file (default to /dev/stdout
                                          with --export, otherwise required)
            --itemized-subscriptions      Export one subscription per row,
                                          only process update subscriptions on
                                          import
            --organization ORGANIZATION   Only process organization matching
                                          this name
            --search SEARCH               Only export search results
            -h, --help                    print help
            -v, --verbose                 be verbose
        """
        cls.command_sub = 'activation-keys'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def content_hosts(cls, options=None):
        """import or export content hosts

        hammer csv content-hosts --help

        Usage::

            hammer csv content-hosts [OPTIONS]

        Options::

            --clear-subscriptions         When processing
                                          --itemized-subscriptions, clear
                                          existing subscriptions first
            --columns COLUMN_NAMES        Comma separated list of column names
                                          to export
            --continue-on-error           Continue processing even if
                                          individual resource error
            --export                      Export current data instead of
                                          importing
            --file FILE_NAME              CSV file (default to /dev/stdout with
                                          --export, otherwise required)
            --itemized-subscriptions      Export one subscription per row, only
                                          process update subscriptions on
                                          import
            --organization ORGANIZATION   Only process organization matching
                                          this name
            --search SEARCH               Only export search results
            -h, --help                    print help
            -v, --verbose                 be verbose

        Columns::

            Name                    - Name of resource
            Search                  - Search for matching names during import
                                    (overrides 'Name' column)
            Organization            - Organization name
            Environment             - Lifecycle environment name
            Content View            - Content view name
            Host Collections        - Comma separated list of host collection
                                    names
            Virtual                 - Is a virtual host, Yes or No
            Guest of Host           - Hypervisor host name for virtual hosts
            OS                      - Operating system
            Arch                    - Architecture
            Sockets                 - Number of sockets
            RAM                     - Quantity of RAM in bytes
            Cores                   - Number of cores
            SLA                     - Service Level Agreement value
            Products                - Comma separated list of products, each of
                                    the format "<sku>|<name>"
            Subscriptions           - Comma separated list of subscriptions,
                                    each of the format "<quantity>|<sku>|<name>
                                    |<contract>|<account>"
            Subscription Name       - Subscription name (only applicable for
                                    --itemized-subscriptions)
            Subscription Type       - Subscription type (only applicable for
                                    --itemized-subscriptions)
            Subscription Quantity   - Subscription quantity (only applicable
                                    for --itemized-subscriptions)
            Subscription SKU        - Subscription SKU (only applicable for
                                    --itemized-subscriptions)
            Subscription Contract   - Subscription contract number (only
                                    applicable for --itemized-subscriptions)
            Subscription Account    - Subscription account number (only
                                    applicable for --itemized-subscriptions)
            Subscription Start      - Subscription start date (only applicable
                                    for --itemized-subscriptions)
            Subscription End        - Subscription end date (only applicable
                                    for --itemized-subscriptions)
        """
        cls.command_sub = 'content-hosts'
        return cls.execute(cls._construct_command(options))

    @classmethod
    def subscriptions(cls, options=None):
        """Import or export subscriptions

        Usage::

            hammer csv subscriptions [OPTIONS]

        Options::

            --continue-on-error           Continue processing even if
                                          individual resource error
            --export                      Export current data instead of
                                          importing
            --file FILE_NAME              CSV file (default to /dev/stdout with
                                          --export, otherwise required)
            --organization ORGANIZATION   Only process organization matching
                                          this name
            --search SEARCH               Only export search results
        """
        cls.command_sub = 'subscriptions'
        return cls.execute(cls._construct_command(options))
