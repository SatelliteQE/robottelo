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

    Supported modes are ipv4 and ipv6. Dual-stack Satellite installs are no
    longer a first-class network type.
    """

    IPV4 = 'ipv4'
    IPV6 = 'ipv6'

    @property
    def has_ipv4(self):
        return self == self.IPV4

    @property
    def has_ipv6(self):
        return self == self.IPV6

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_scalar('!NetworkType', node.value)

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_scalar(node)
        return cls(value)


@yaml.register_class
class InstallMethod(StrEnum):
    """
    Enumeration of Satellite installation methods.

    This enum represents the different methods that can be used to install
    Satellite/Foreman on a system.
    """

    INSTALLER = 'installer'  # Traditional satellite-installer
    FOREMANCTL = 'foremanctl'  # New foremanctl deploy
    AUTO = 'auto'  # Auto-detect based on system state

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_scalar('!InstallMethod', node.value)

    @classmethod
    def from_yaml(cls, constructor, node):
        value = constructor.construct_scalar(node)
        return cls(value)
