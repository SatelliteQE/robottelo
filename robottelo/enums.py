"""Module containing enumeration classes used throughout Robottelo.

This module provides standardized enumerations for various types, statuses,
and configurations used in Robottelo tests and utilities.
"""

from enum import StrEnum


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
    def formatted(self):
        """
        Returns the properly formatted version of the network type (e.g., 'IPv4', 'IPv6')

        :returns: The formatted network type as a string.
        :rtype: str
        :raises ValueError: If called on DUALSTACK
        """
        if self.value == 'dualstack':
            raise ValueError(f'Formatted property not supported for {self.name}')
        if self.value in (self.IPV4, self.IPV6):
            return self.value.replace('ipv', 'IPv')
        raise ValueError(f'Invalid network type: {self.value}')
