"""
Usage::

    hammer content-view [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    add-repository                Associate a resource
    add-version                   Update a content view
    component                     View and manage components
    copy                          Copy a content view
    create                        Create a content view
    delete                        Delete a content view
    filter                        View and manage filters
    info                          Show a content view
    list                          List content views
    publish                       Publish a content view
    remove                        Remove versions and/or environments from a
                                  content view and reassign systems and keys
    remove-from-environment       Remove a content view from an environment
    remove-repository             Disassociate a resource
    remove-version                Remove a content view version from a
                                  composite view
    update                        Update a content view
    version                       View and manage content view versions

Options::

    -h, --help                    print help
"""
from robottelo.cli import hammer
from robottelo.cli.base import Base
from robottelo.cli.base import CLIError


class ContentViewFilterRule(Base):
    """Manipulates content view filter rules."""

    command_base = 'content-view filter rule'

    @classmethod
    def create(cls, options=None):
        """Create a content-view filter rule"""
        if (
            not options
            or 'content-view-filter' not in options
            and 'content-view-filter-id' not in options
        ):
            raise CLIError(
                'Could not find content_view_filter, please set one of options'
                ' "content-view-filter" or "content-view-filter-id".'
            )
        cls.command_sub = 'create'
        result = cls.execute(cls._construct_command(options), output_format='csv')

        # Extract new CV filter rule ID if it was successfully created
        if len(result) > 0 and 'id' in result[0]:
            cvfr_id = result[0]['id']
            # CV filter rule can only be fetched by specifying either
            # content-view-filter-id or content-view-filter + content-view-id.
            # Passing these options to info command
            info_options = {
                'content-view-id': options.get('content-view-id'),
                'content-view-filter': options.get('content-view-filter'),
                'content-view-filter-id': options.get('content-view-filter-id'),
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

    filter = ContentViewFilter

    @classmethod
    def add_repository(cls, options):
        """Associate repository to a selected CV."""
        cls.command_sub = 'add-repository'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def add_version(cls, options):
        """Associate version to a selected CV."""
        cls.command_sub = 'add-version'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def copy(cls, options):
        """Copy existing content-view to a new one"""
        cls.command_sub = 'copy'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def publish(cls, options, timeout=1500000):
        """Publishes a new version of content-view."""
        cls.command_sub = 'publish'
        return cls.execute(cls._construct_command(options), ignore_stderr=True, timeout=timeout)

    @classmethod
    def version_info(cls, options, output_format=None):
        """Provides version info related to content-view's version."""
        cls.command_sub = 'version info'

        if options is None:
            options = {}

        result = cls.execute(cls._construct_command(options), output_format=output_format)
        if output_format != 'json':
            result = hammer.parse_info(result)
        return result

    @classmethod
    def version_incremental_update(cls, options):
        """Performs incremental update of the content-view's version"""
        cls.command_sub = 'version incremental-update'
        if options is None:
            options = {}
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def version_list(cls, options):
        """Lists content-view's versions."""
        cls.command_sub = 'version list'
        if options is None:
            options = {}
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def version_promote(cls, options, timeout=600000):
        """Promotes content-view version to next env."""
        cls.command_sub = 'version promote'
        return cls.execute(cls._construct_command(options), ignore_stderr=True, timeout=timeout)

    @classmethod
    def version_export(cls, options, timeout=300000):
        """Exports content-view version in given directory"""
        cls.command_sub = 'version export'
        return cls.execute(cls._construct_command(options), ignore_stderr=True, timeout=timeout)

    @classmethod
    def version_import(cls, options, timeout=300000):
        """Imports content-view version from a given directory"""
        cls.command_sub = 'version import'
        return cls.execute(cls._construct_command(options), ignore_stderr=True, timeout=timeout)

    @classmethod
    def version_delete(cls, options):
        """Removes content-view version."""
        cls.command_sub = 'version delete'
        return cls.execute(cls._construct_command(options), ignore_stderr=True)

    @classmethod
    def remove_from_environment(cls, options=None):
        """Remove content-view from an environment"""
        cls.command_sub = 'remove-from-environment'
        return cls.execute(cls._construct_command(options), ignore_stderr=True)

    @classmethod
    def remove(cls, options=None):
        """Remove versions and/or environments from a content view and
        reassign content hosts and keys
        """
        cls.command_sub = 'remove'
        return cls.execute(cls._construct_command(options), ignore_stderr=True)

    @classmethod
    def remove_version(cls, options=None):
        """Remove a content view version from a composite view"""
        cls.command_sub = 'remove-version'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def remove_repository(cls, options):
        """Remove repository from content view"""
        cls.command_sub = 'remove-repository'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def component_add(cls, options=None):
        """Add components to the content view"""
        cls.command_sub = 'component add'
        return cls.execute(cls._construct_command(options), output_format='csv')

    @classmethod
    def component_list(cls, options=None):
        """List components attached to the content view"""
        cls.command_sub = 'component list'
        return cls.execute(cls._construct_command(options), output_format='csv')
