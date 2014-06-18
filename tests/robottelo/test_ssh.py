"""Tests for module ``robottelo.common.ssh``."""
# (too-many-public-methods) pylint: disable=R0904
from paramiko.ssh_exception import AuthenticationException
from robottelo.common import conf, get_app_root
from robottelo.common.ssh import _get_connection
from unittest import TestCase
import os
import socket


class SSHTestCase(TestCase):
    """Tests for module ``robottelo.common.ssh``."""
    def test__get_connection(self):
        """Test method ``_get_connection``.

        Attempt to make an SSH connection to localhost. Assert that the
        connection is refused.

        """
        # pylint: disable=W0212
        backup = conf.properties
        conf.properties['main.server.hostname'] = 'localhost'
        conf.properties['main.server.ssh.username'] = 'nobody'
        conf.properties['main.server.ssh.key_private'] = os.path.join(
            get_app_root(), 'tests', 'robottelo', 'data', 'test_dsa.key'
        )
        with self.assertRaises((socket.error, AuthenticationException)):
            with _get_connection() as connection:  # flake8: noqa pylint: disable=W0612
                pass
        conf.properties = backup
