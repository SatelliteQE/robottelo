"""Tests for module ``robottelo.ssh``."""
# (too-many-public-methods) pylint: disable=R0904
import os

from robottelo import ssh
from robottelo.config import conf, get_app_root
from unittest2 import TestCase


class MockSSHClient(object):
    """A mock ``paramiko.SSHClient`` object."""
    def __init__(self):
        """Set several debugging counters to 0.

        Whenever a method in this mock class is called, a corresponding counter
        is incremented. For example, if ``connect`` is called, then
        ``connect_`` is incremented by 1.

        """
        # These are counters for logging function calls
        self.set_missing_host_key_policy_ = 0
        self.connect_ = 0
        self.close_ = 0
        # The tests look for these vars
        self.hostname = None
        self.username = None
        self.key_filename = None

    def set_missing_host_key_policy(self, policy):  # pylint:disable=W0613
        """A no-op stub method."""
        self.set_missing_host_key_policy_ += 1

    def connect(  # pylint:disable=W0613,R0913
            self, hostname, port=22, username=None, password=None, pkey=None,
            key_filename=None, timeout=None, allow_agent=True,
            look_for_keys=True, compress=False, sock=None):
        """"A stub method that records some of the parameters passed in.

        When this method is called, the following arguments are recorded as
        instance attributes:

        * hostname
        * username
        * key_filename

        """
        self.connect_ += 1
        self.hostname = hostname
        self.username = username
        self.key_filename = key_filename

    def close(self):
        """A no-op stub method."""
        self.close_ += 1


class SSHTestCase(TestCase):
    """Tests for module ``robottelo.ssh``."""
    def test__get_connection(self):
        """Test method ``_get_connection``.

        Mock up ``paramiko.SSHClient`` (by overriding method
        ``_call_paramiko_sshclient``) before calling ``_get_connection``.
        Assert that certain parameters are passed to the (mock)
        ``paramiko.SSHClient`` object, and that certain methods on that object
        are called.

        """
        ssh._call_paramiko_sshclient = MockSSHClient  # pylint:disable=W0212
        backup = conf.properties

        key_filename = os.path.join(
            get_app_root(), 'tests', 'robottelo', 'data', 'test_dsa.key'
        )
        conf.properties['main.server.hostname'] = 'example.com'
        conf.properties['main.server.ssh.username'] = 'nobody'
        conf.properties['main.server.ssh.key_private'] = key_filename
        with ssh._get_connection() as connection:  # pylint:disable=W0212
            self.assertEqual(connection.set_missing_host_key_policy_, 1)
            self.assertEqual(connection.connect_, 1)
            self.assertEqual(connection.close_, 0)
            self.assertEqual(connection.hostname, 'example.com')
            self.assertEqual(connection.username, 'nobody')
            self.assertEqual(connection.key_filename, key_filename)
        self.assertEqual(connection.set_missing_host_key_policy_, 1)
        self.assertEqual(connection.connect_, 1)
        self.assertEqual(connection.close_, 1)

        conf.properties = backup
