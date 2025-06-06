"""Tests for Robottelo's enumeration classes."""

from robottelo.enums import NetworkType


class TestNetworkType:
    """Tests for the NetworkType enum class."""

    def test_enum_values(self):
        """Test that the enum has the expected values."""
        assert NetworkType.IPV4 == 'ipv4'
        assert NetworkType.IPV6 == 'ipv6'
        assert NetworkType.DUALSTACK == 'dualstack'

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

    def test_has_ipv4_property(self):
        """Test the has_ipv4 property for all network types."""
        assert NetworkType.IPV4.has_ipv4 is True
        assert NetworkType.IPV6.has_ipv4 is False
        assert NetworkType.DUALSTACK.has_ipv4 is True

    def test_has_ipv6_property(self):
        """Test the has_ipv6 property for all network types."""
        assert NetworkType.IPV4.has_ipv6 is False
        assert NetworkType.IPV6.has_ipv6 is True
        assert NetworkType.DUALSTACK.has_ipv6 is True
