# -*- encoding: utf-8 -*-
"""
Usage::

    hammer content-host [OPTIONS] SUBCOMMAND [ARG] ...

Parameters::

    SUBCOMMAND                    subcommand
    [ARG] ...                     subcommand arguments

Subcommands::

    available-incremental-updates Given a set of systems and errata, lists the
                                  content view versions and environments that
                                  need updating.
    create                        Register a content host
    delete                        Unregister a content host
    info                          Show a content host
    list                          List content hosts
    tasks
    update                        Update content host information

"""
from robottelo.cli.base import Base
from robottelo.cli.host import Host
from robottelo.decorators import affected_by_bz


class ContentHost(Base):
    """Manipulates Katello engine's content-host command."""
    command_base = 'content-host'

    @classmethod
    def create(cls, options=None):
        """Work around host unification not being completed in order to create
        a new content host which is now a host subscription.
        """
        if 'organization-id' in options and options['organization-id']:
            organization_field = 'organization-id'
            organization_value = options['organization-id']
        else:
            for key, value in options.items():
                if key.startswith('organization') and value:
                    organization_field = key
                    organization_value = value
        content_host = Host.subscription_register(options)
        if affected_by_bz(1328202):
            results = ContentHost.list({
                organization_field: organization_value,
            })
            # Content host registration converts the name to lowercase, make
            # sure to use the same format while matching against the result
            content_host_name = options.get('name').lower()
            for result in results:
                if result['name'] == content_host_name:
                    content_host = result
        return ContentHost.info({'id': content_host['id']})

    @classmethod
    def delete(cls, options=None):
        """Work around host unification not being completed in order to delete
        a content host which is now a host subscription.
        """
        # Replace content host id with host id if passed
        if 'host-id' in options:
            name = ContentHost.info({'id': options['host-id']})['name'].lower()
            options['host-id'] = Host.info({'name': name})['id']
        return Host.subscription_unregister(options)

    @classmethod
    def tasks(cls, options=None):
        """Lists async tasks for a content host."""
        cls.command_sub = 'tasks'
        return cls.execute(
            cls._construct_command(options), output_format='csv')
