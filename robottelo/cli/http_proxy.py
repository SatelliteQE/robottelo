"""
Usage:
     http-proxy [OPTIONS] SUBCOMMAND [ARG] ...

Parameters:
 SUBCOMMAND                    Subcommand
 [ARG] ...                     Subcommand arguments

Subcommands:
 create                        Create an HTTP Proxy
 delete                        Delete an HTTP Proxy
 info                          Show an HTTP Proxy
 list                          List of HTTP Proxies
 update                        Update an HTTP Proxy

Options:
 -h, --help                    Print help
"""

from robottelo.cli.base import Base


class HttpProxy(Base):
    """Manipulates http-proxy command."""

    command_base = 'http-proxy'
