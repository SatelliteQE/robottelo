"""Module containing enumeration classes used throughout Robottelo.

This module provides standardized enumerations for various types, statuses,
and configurations used in Robottelo tests and utilities.
"""

from enum import Enum

# TODO: change double quotes to single quotes bcs of consistency


class HostNetworkType(Enum):
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
        if self.value in (self.IVP4):
            return self.value.replace('ipv', 'IPv')
        raise ValueError(f'Invalid network type: {self.value}')

    def __str__(self):
        """
        Returns the string representation of the enum member.

        :returns: The string value of the enum member.
        :rtype: str
        """
        return self.value

    def __eq__(self, other):
        """
        Implements equality comparison between enum members and strings.

        This allows direct comparison of enum members with their string values:
        HostNetworkType.IPV4 == 'ipv4'  # True

        :param other: The object to compare with
        :return: True if equal, False otherwise
        :rtype: bool
        """
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

    @classmethod
    def list_values(cls):
        """
        Return a set of all enum values.

        :returns: A set containing all the string values of the enum members.
        :rtype: set
        """
        return {nt.value for nt in cls}
