"""Tests for module ``robottelo.ssh``."""
import os
from io import StringIO
from unittest import mock

import paramiko

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
        allow_agent=True,
        look_for_keys=True,
        compress=False,
        sock=None,
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

    def exec_command(self, cmd, *args, **kwargs):
        return (self.ret_code, MockStdout(cmd, self.ret_code), MockStdout('', self.ret_code))


class TestSSH:
    """Tests for module ``robottelo.ssh``."""

    @mock.patch('robottelo.config.settings')
    def test_get_connection_key(self, settings):
        """Test method ``get_connection`` using key file to connect to the
        server.

        Mock up ``paramiko.SSHClient`` (by overriding method
        ``_call_paramiko_sshclient``) before calling ``get_connection``.
        Assert that certain parameters are passed to the (mock)
        ``paramiko.SSHClient`` object, and that certain methods on that object
        are called.
        """
        ssh._call_paramiko_sshclient = MockSSHClient

        key_filename = os.path.join(os.path.abspath(__name__), 'data', 'test_dsa.key')
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_password = None
        settings.server.ssh_key = key_filename
        settings.server.ssh_key_string = None
        settings.server.ssh_client.command_timeout = 300
        settings.server.ssh_client.connection_timeout = 10
        with ssh.get_connection() as connection:
            assert connection.set_missing_host_key_policy_ == 1
            assert connection.connect_ == 1
            assert connection.close_ == 0
            assert connection.hostname == 'example.com'
            assert connection.username == 'nobody'
            assert connection.key_filename == key_filename
            assert connection.password is None
            assert connection.pkey is None
        assert connection.set_missing_host_key_policy_ == 1
        assert connection.connect_ == 1
        assert connection.close_ == 1

    @mock.patch('robottelo.config.settings')
    def test_get_connection_pass(self, settings):
        """Test method ``get_connection`` using password of user to connect to
        the server

        Mock up ``paramiko.SSHClient`` (by overriding method
        ``_call_paramiko_sshclient``) before calling ``get_connection``.
        Assert that certain parameters are passed to the (mock)
        ``paramiko.SSHClient`` object, and that certain methods on that object
        are called.
        """
        ssh._call_paramiko_sshclient = MockSSHClient
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.server.ssh_key_string = None
        settings.server.ssh_client.command_timeout = 300
        settings.server.ssh_client.connection_timeout = 10
        with ssh.get_connection() as connection:
            assert connection.set_missing_host_key_policy_ == 1
            assert connection.connect_ == 1
            assert connection.close_ == 0
            assert connection.hostname == 'example.com'
            assert connection.username == 'nobody'
            assert connection.password == 'test_password'
            assert connection.key_filename is None
            assert connection.pkey is None
        assert connection.set_missing_host_key_policy_ == 1
        assert connection.connect_ == 1
        assert connection.close_ == 1

    @mock.patch('robottelo.config.settings')
    def test_get_connection_key_string(self, settings):
        """Test method ``get_connection`` using key file to connect to the
        server.

        Mock up ``paramiko.SSHClient`` (by overriding method
        ``_call_paramiko_sshclient``) before calling ``get_connection``.
        Assert that certain parameters are passed to the (mock)
        ``paramiko.SSHClient`` object, and that certain methods on that object
        are called.
        """
        ssh._call_paramiko_sshclient = MockSSHClient
        key_string = StringIO('')
        rsa_key = paramiko.rsakey.RSAKey.generate(512)
        rsa_key.write_private_key(key_string)
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_password = None
        settings.server.ssh_key = None
        settings.server.ssh_key_string = key_string.getvalue()  # resolve StringIO stream
        settings.server.ssh_client.command_timeout = 300
        settings.server.ssh_client.connection_timeout = 10
        with ssh.get_connection() as connection:
            assert connection.set_missing_host_key_policy_ == 1
            assert connection.connect_ == 1
            assert connection.close_ == 0
            assert connection.hostname == 'example.com'
            assert connection.username == 'nobody'
            assert connection.password is None
            assert connection.key_filename is None
            assert connection.pkey == rsa_key  # PKey.__cmp__
        assert connection.set_missing_host_key_policy_ == 1
        assert connection.connect_ == 1
        assert connection.close_ == 1

    @mock.patch('robottelo.config.settings')
    def test_execute_command(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.server.ssh_client.command_timeout = 300
        settings.server.ssh_client.connection_timeout = 10

        with ssh.get_connection() as connection:
            ret = ssh.execute_command('ls -la', connection)
            assert ret.stdout == ['ls -la']
            assert isinstance(ret, ssh.SSHCommandResult)

    @mock.patch('robottelo.config.settings')
    def test_execute_command_base_output(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.server.ssh_client.command_timeout = 300
        settings.server.ssh_client.connection_timeout = 10

        with ssh.get_connection() as connection:
            ret = ssh.execute_command('ls -la', connection, output_format='base')
            assert ret.stdout == 'ls -la'
            assert isinstance(ret, ssh.SSHCommandResult)

    @mock.patch('robottelo.config.settings')
    def test_command(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.server.ssh_client.command_timeout = 300
        settings.server.ssh_client.connection_timeout = 10

        ret = ssh.command('ls -la')
        assert ret.stdout == ['ls -la']
        assert isinstance(ret, ssh.SSHCommandResult)

    @mock.patch('robottelo.config.settings')
    def test_command_base_output(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.server.ssh_client.command_timeout = 300
        settings.server.ssh_client.connection_timeout = 10

        ret = ssh.command('ls -la', output_format='base')
        assert ret.stdout == 'ls -la'
        assert isinstance(ret, ssh.SSHCommandResult)

    @mock.patch('robottelo.config.settings')
    def test_parse_csv(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.server.ssh_client.command_timeout = 300
        settings.server.ssh_client.connection_timeout = 10

        ret = ssh.command('a,b,c\n1,2,3', output_format='csv')
        assert ret.stdout == [{'a': '1', 'b': '2', 'c': '3'}]
        assert isinstance(ret, ssh.SSHCommandResult)

    @mock.patch('robottelo.config.settings')
    def test_parse_json(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.server.ssh_client.command_timeout = 300
        settings.server.ssh_client.connection_timeout = 10

        ret = ssh.command('{"a": 1, "b": true}', output_format='json')
        assert ret.stdout == {'a': '1', 'b': True}
        assert isinstance(ret, ssh.SSHCommandResult)

    def test_call_paramiko_client(self):
        assert isinstance(ssh._call_paramiko_sshclient(), (paramiko.SSHClient, MockSSHClient))
