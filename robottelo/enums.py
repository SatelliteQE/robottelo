"""Module containing enumeration classes used throughout Robottelo.

This module provides standardized enumerations for various types, statuses,
and configurations used in Robottelo tests and utilities.
"""

from enum import StrEnum

import ruamel.yaml

yaml = ruamel.yaml.YAML()


@yaml.register_class
class NetworkType(StrEnum):
    """
    Enumeration of host network addressing types.

    This enum represents the different network addressing modes that can be
    configured for a host.
    """

    IPV4 = 'ipv4'
    IPV6 = 'ipv6'
    DUALSTACK = 'dualstack'

    @property
    def has_ipv4(self):
        return self in (self.IPV4, self.DUALSTACK)

    @property
    def has_ipv6(self):
        return self in (self.IPV6, self.DUALSTACK)

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_scalar('!NetworkType', node.value)

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_scalar(node)
        return cls(value)
