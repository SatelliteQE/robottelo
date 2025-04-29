"""Tests for Robottelo's enumeration classes."""

import pytest

from robottelo.enums import NetworkType


class TestNetworkType:
    """Tests for the NetworkType enum class."""

    def test_enum_values(self):
        """Test that the enum has the expected values."""
        assert NetworkType.IPV4 == 'ipv4'
        assert NetworkType.IPV6 == 'ipv6'
        assert NetworkType.DUALSTACK == 'dualstack'

    def test_formatted_property_ipv4(self):
        """Test the formatted property for IPV4."""
        assert NetworkType.IPV4.formatted == 'IPv4'

    def test_formatted_property_dualstack(self):
        """Test that formatted property raises ValueError for DUALSTACK."""
        error_msg = 'Formatted property not supported for DUALSTACK'
        with pytest.raises(ValueError, match=error_msg) as excinfo:
            _ = NetworkType.DUALSTACK.formatted
        assert 'not supported for DUALSTACK' in str(excinfo.value)

    def test_str_representation(self):
        """Test the string representation of enum members."""
        assert str(NetworkType.IPV4) == 'ipv4'
        assert str(NetworkType.IPV6) == 'ipv6'
        assert str(NetworkType.DUALSTACK) == 'dualstack'

    def test_equality_with_string(self):
        """Test equality comparison between enum members and strings."""
        assert NetworkType.IPV4 == 'ipv4'
        assert NetworkType.IPV6 == 'ipv6'
        assert NetworkType.DUALSTACK == 'dualstack'
        assert NetworkType.IPV4 != 'ipv6'
        assert NetworkType.IPV6 != 'ipv4'

    def test_equality_with_enum(self):
        """Test equality comparison between enum members."""
        assert NetworkType.IPV4 == NetworkType.IPV4
        assert NetworkType.IPV4 != NetworkType.IPV6
        assert NetworkType.IPV6 != NetworkType.DUALSTACK
