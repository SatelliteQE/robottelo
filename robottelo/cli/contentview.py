# -*- encoding: utf-8 -*-
"""
Usage::

    hammer content-view [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add-repository                Associate a resource
    add-version                   Update a content view
    copy                          Copy a content view
    create                        Create a content view
    delete                        Delete a content view
    filter                        View and manage filters
    info                          Show a content view
    list                          List content views
    publish                       Publish a content view
    puppet-module                 View and manage puppet modules
    remove                        Remove versions and/or environments from a
                                  content view and reassign systems and keys
    remove-from-environment       Remove a content view from an environment
    remove-repository             Disassociate a resource
    remove-version                Disassociate a resource
    update                        Update a content view
    version                       View and manage content view versions

Options::

    -h, --help                    print help
"""

from robottelo.cli import hammer
from robottelo.cli.base import Base, CLIError


class ContentViewFilterRule(Base):
    """Manipulates content view filter rules."""

    command_base = 'content-view filter rule'

    @classmethod
    def create(cls, options=None):
        """Create a content-view filter rule"""
        if (
                not options or
                'content-view-filter' not in options and
                'content-view-filter-id' not in options):
            raise CLIError(
                'Could not find content_view_filter, please set one of options'
                ' "content-view-filter" or "content-view-filter-id".'
            )
        cls.command_sub = 'create'
        result = cls.execute(
            cls._construct_command(options), output_format='csv')

        # Extract new CV filter rule ID if it was successfully created
        if len(result) > 0 and 'id' in result[0]:
            cvfr_id = result[0]['id']
            # CV filter rule can only be fetched by specifying either
            # content-view-filter-id or content-view-filter + content-view-id.
            # Passing these options to info command
            info_options = {
                'content-view-id': options.get('content-view-id'),
                'content-view-filter': options.get('content-view-filter'),
                'content-view-filter-id': options.get(
                    'content-view-filter-id'),
                'id': cvfr_id,
            }
            result = cls.info(info_options)
        return result


class ContentViewFilter(Base):
    """Manipulates content view filters."""

    command_base = 'content-view filter'

    rule = ContentViewFilterRule


class ContentView(Base):
    """Manipulates Foreman's content view."""

    command_base = 'content-view'

    @classmethod
    def add_repository(cls, options):
        """Associate repository to a selected CV."""
        cls.command_sub = 'add-repository'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def add_version(cls, options):
        """Associate version to a selected CV."""
        cls.command_sub = 'add-version'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def copy(cls, options):
        """Copy existing content-view to a new one"""
        cls.command_sub = 'copy'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def publish(cls, options, timeout=None):
        """Publishes a new version of content-view."""
        cls.command_sub = 'publish'
        # Publishing can take a while so try to wait a bit longer
        if timeout is None:
            timeout = 120
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
            timeout=timeout,
        )

    @classmethod
    def version_info(cls, options):
        """Provides version info related to content-view's version."""
        cls.command_sub = 'version info'

        if options is None:
            options = {}

        return hammer.parse_info(cls.execute(cls._construct_command(options)))

    @classmethod
    def version_incremental_update(cls, options):
        """Performs incremental update of the content-view's version"""
        cls.command_sub = 'version incremental-update'
        if options is None:
            options = {}
            return cls.execute(
                cls._construct_command(options),
                output_format='info'
            )

    @classmethod
    def puppet_module_add(cls, options):
        """Associate puppet_module to selected CV"""
        cls.command_sub = 'puppet-module add'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def puppet_module_list(cls, options):
        """List content view puppet modules"""
        cls.command_sub = 'puppet-module list'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def puppet_module_remove(cls, options):
        """Remove a puppet module from the content view"""
        cls.command_sub = 'puppet-module remove'
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def filter_info(cls, options):
        """Provides filter info related to content-view's version."""

        cls.command_sub = 'filter info'

        if options is None:
            options = {}

        return hammer.parse_info(cls.execute(cls._construct_command(options)))

    @classmethod
    def filter_create(cls, options):
        """Add new filter to content view entity.

        Usage::

            hammer content-view filter create [OPTIONS]

        Options::

            --content-view CONTENT_VIEW_NAME    Content view name
            --content-view-id CONTENT_VIEW_ID   Content view numeric identifier
            --description DESCRIPTION           Description of the filter
            --inclusion INCLUSION               Specifies if content should be
                                                included or excluded, default:
                                                inclusion=false (One of yes/no,
                                                1/0, true/false)
            --name NAME                         name of the filter
            --organization ORGANIZATION_NAME    Organization name to search by
            --organization-id ORGANIZATION_ID   Organization ID
            --organization-label ORGANIZATION_LABEL   Organization label to
                                                      search by
            --original-packages ORIGINAL_PACKAGES     Add all packages without
                                                      Errata to the included/
                                                      excluded list. (Package
                                                      Filter only)
            --repositories REPOSITORY_NAMES      Comma separated list of values
            --repository-ids REPOSITORY_IDS      Repository ID
            --type TYPE                          type of filter (e.g. rpm,
                                                 package_group, erratum)
        """
        cls.command_sub = 'filter create'
        if options is None:
            options = {}
        result = cls.execute(
            cls._construct_command(options), output_format='csv')
        if isinstance(result, list):
            result = result[0]
        return result

    @classmethod
    def filter_update(cls, options):
        """Update existing content view filter entity.

        Usage::

            hammer content-view filter update [OPTIONS]

        Options::

            --content-view CONTENT_VIEW_NAME    Content view name
            --content-view-id CONTENT_VIEW_ID   Content view numeric identifier
            --id ID                             filter identifier
            --inclusion INCLUSION               Specifies if content should be
                                                included or excluded, default:
                                                inclusion=false (One of yes/no,
                                                1/0, true/false)
            --name NAME                         Name to search by
            --new-name NEW_NAME                 new name for the filter
            --organization ORGANIZATION_NAME    Organization name to search by
            --organization-id ORGANIZATION_ID   Organization ID
            --organization-label ORGANIZATION_LABEL   Organization label to
                                                      search by
            --original-packages ORIGINAL_PACKAGES     Add all packages without
                                                      Errata to the included/
                                                      excluded list. (Package
                                                      Filter only)
            --repositories REPOSITORY_NAMES      Repository Name
                                                 Comma separated list of values
            --repository-ids REPOSITORY_IDS      Repository ID
                                                 Comma separated list of values

        """
        cls.command_sub = 'filter update'
        if options is None:
            options = {}
        return cls.execute(cls._construct_command(options))

    @classmethod
    def filter_delete(cls, options):
        """Delete existing content view filter entity.

        Usage::

            hammer content-view filter delete [OPTIONS]

        Options::

            --content-view CONTENT_VIEW_NAME    Content view name
            --content-view-id CONTENT_VIEW_ID   Content view numeric identifier
            --id ID                             filter identifier
            --name NAME                         Name to search by
            --organization ORGANIZATION_NAME    Organization name to search by
            --organization-id ORGANIZATION_ID   Organization ID
            --organization-label ORGANIZATION_LABEL   Organization label to
                                                      search by

        """
        cls.command_sub = 'filter delete'
        if options is None:
            options = {}
        return cls.execute(cls._construct_command(options))

    @classmethod
    def filter_rule_create(cls, options):
        """Add new rule to content view filter."""
        cls.command_sub = 'filter rule create'
        if options is None:
            options = {}
        return cls.execute(cls._construct_command(options))

    @classmethod
    def version_list(cls, options):
        """Lists content-view's versions."""
        cls.command_sub = 'version list'
        if options is None:
            options = {}
        return cls.execute(
            cls._construct_command(options), output_format='csv')

    @classmethod
    def version_promote(cls, options):
        """Promotes content-view version to next env."""
        cls.command_sub = 'version promote'
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
        )

    @classmethod
    def version_delete(cls, options):
        """Removes content-view version."""
        cls.command_sub = 'version delete'
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
        )

    @classmethod
    def remove_from_environment(cls, options=None):
        """Remove content-view from an environment"""
        cls.command_sub = 'remove-from-environment'
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
        )

    @classmethod
    def remove(cls, options=None):
        """Remove versions and/or environments from a content view and
        reassign content hosts and keys

        """
        cls.command_sub = 'remove'
        return cls.execute(
            cls._construct_command(options),
            ignore_stderr=True,
        )
