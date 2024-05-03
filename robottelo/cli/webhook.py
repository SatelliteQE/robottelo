"""
Usage:
    hammer webhook [OPTIONS] SUBCOMMAND [ARG] ...
Parameters:
 SUBCOMMAND                    Subcommand
 [ARG] ...                     Subcommand arguments
Subcommands:
 create                        Create a Webhook
 delete                        Delete a Webhook
 info                          Show Webhook details
 list                          List Webhooks
 update                        Update a Webhook
Options:
 -h, --help                    Print help
"""

from robottelo.cli.base import Base, CLIError
from robottelo.constants import WEBHOOK_EVENTS, WEBHOOK_METHODS


class Webhook(Base):
    command_base = 'webhook'

    @classmethod
    def create(cls, options=None, timeout=None):
        """Create a webhook"""
        cls.command_sub = 'create'

        if options is None:
            options = dict()

        if options.get('event', None) not in WEBHOOK_EVENTS:
            raise CLIError(
                'The option "event" must be one of predefined events.'
                'See "hammer webhook create --help" for list of allowed events'
            )

        if options.get('http-method', None) not in WEBHOOK_METHODS:
            raise CLIError(
                'The option "method" must be one supported HTTP methods. '
                'See See "hammer webhook create --help" for the list of supported  methods'
            )

        return super().create(options, timeout)
