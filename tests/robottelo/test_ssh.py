"""Tests for module ``robottelo.common.ssh``."""
# (too-many-public-methods) pylint: disable=R0904
from robottelo.common import conf
from robottelo.common.ssh import _get_connection
from unittest import TestCase
import socket


class SSHTestCase(TestCase):
    """Tests for module ``robottelo.common.ssh``."""
    def test__get_connection(self):
        """Test method ``_get_connection``.

        Attempt to make an SSH connection to localhost. Assert that the
        connection is refused.

        """
        # pylint: disable=W0212
        backup = conf._properties
        conf._properties['main.server.hostname'] = 'localhost'
        with self.assertRaises(socket.error):
            with _get_connection() as connection:  # flake8: noqa pylint: disable=W0612
                pass
        conf._properties = backup
