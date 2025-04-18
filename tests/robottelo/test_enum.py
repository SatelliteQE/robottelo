"""Tests for Robottelo's enumeration classes."""

import pytest

from robottelo.enums import HostNetworkType


class TestHostNetworkType:
    """Tests for the HostNetworkType enum class."""

    def test_enum_values(self):
        """Test that the enum has the expected values."""
        assert HostNetworkType.IPV4 == 'ipv4'
        assert HostNetworkType.IPV6 == 'ipv6'
        assert HostNetworkType.DUALSTACK == 'dualstack'

    def test_formatted_property_ipv4(self):
        """Test the formatted property for IPV4."""
        assert HostNetworkType.IPV4.formatted == 'IPv4'

    def test_formatted_property_dualstack(self):
        """Test that formatted property raises ValueError for DUALSTACK."""
        error_msg = 'Formatted property not supported for DUALSTACK'
        with pytest.raises(ValueError, match=error_msg) as excinfo:
            _ = HostNetworkType.DUALSTACK.formatted
        assert 'not supported for DUALSTACK' in str(excinfo.value)

    def test_str_representation(self):
        """Test the string representation of enum members."""
        assert str(HostNetworkType.IPV4) == 'ipv4'
        assert str(HostNetworkType.IPV6) == 'ipv6'
        assert str(HostNetworkType.DUALSTACK) == 'dualstack'

    def test_equality_with_string(self):
        """Test equality comparison between enum members and strings."""
        assert HostNetworkType.IPV4 == 'ipv4'
        assert HostNetworkType.IPV6 == 'ipv6'
        assert HostNetworkType.DUALSTACK == 'dualstack'
        assert HostNetworkType.IPV4 != 'ipv6'
        assert HostNetworkType.IPV6 != 'ipv4'

    def test_equality_with_enum(self):
        """Test equality comparison between enum members."""
        assert HostNetworkType.IPV4 == HostNetworkType.IPV4
        assert HostNetworkType.IPV4 != HostNetworkType.IPV6
        assert HostNetworkType.IPV6 != HostNetworkType.DUALSTACK

    def test_list_values(self):
        """Test the list_values class method."""
        expected = {'ipv4', 'ipv6', 'dualstack'}
        assert HostNetworkType.list_values() == expected
