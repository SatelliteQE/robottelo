"""Tests for module ``robottelo.utils.ssh``."""
from unittest import mock

from robottelo import ssh


class MockChannel:
    def __init__(self, ret, status_ready=True):
        self.ret = ret
        self.status_ready = status_ready

    def recv_exit_status(self):
        return self.ret

    def exit_status_ready(self):
        return self.status_ready


class MockStdout:
    def __init__(self, cmd, ret):
        self.cmd = cmd
        self.channel = MockChannel(ret=ret)

    def read(self):
        return self.cmd


class MockSSHClient:
    """A mock ``broker.Host`` object."""

    def __init__(self, **kwargs):
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
        self.pkey = None
        self.password = None
        self.ret_code = 0

    def set_missing_host_key_policy(self, policy):
        """A no-op stub method."""
        self.set_missing_host_key_policy_ += 1

    def connect(
        self,
        hostname,
        port=22,
        username=None,
        password=None,
        pkey=None,
        key_filename=None,
        timeout=None,
    ):
        """ "A stub method that records some of the parameters passed in.

        When this method is called, the following arguments are recorded as
        instance attributes:

        * hostname
        * username
        * key_filename

        """
        self.connect_ += 1
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.pkey = pkey

    def close(self):
        """A no-op stub method."""
        self.close_ += 1

    def execute(self, cmd, *args, **kwargs):
        return (self.ret_code, MockStdout(cmd, self.ret_code), MockStdout('', self.ret_code))


class TestSSH:
    """Tests for module ``robottelo.utils.ssh``."""

    @mock.patch('robottelo.config.settings')
    def test_command(self, settings):
        ssh.get_client = MockSSHClient
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.server.ssh_client.command_timeout = 300000
        settings.server.ssh_client.connection_timeout = 10000

        ret = ssh.command('ls -la')
        assert ret[1].cmd == 'ls -la'
