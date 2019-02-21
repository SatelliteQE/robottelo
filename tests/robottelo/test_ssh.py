"""Tests for module ``robottelo.ssh``."""
# (too-many-public-methods) pylint: disable=R0904
import os
import paramiko
import six

from robottelo import ssh
from unittest2 import TestCase

if six.PY2:
    import mock
else:
    from unittest import mock


class MockChannel(object):
    def __init__(self, ret, status_ready=True):
        self.ret = ret
        self.status_ready = status_ready

    def recv_exit_status(self):
        return self.ret

    def exit_status_ready(self):
        return self.status_ready


class MockStdout(object):
    def __init__(self, cmd, ret):
        self.cmd = cmd
        self.channel = MockChannel(ret=ret)

    def read(self):
        return self.cmd


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
        self.password = None
        self.ret_code = 0

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
        self.password = password
        self.key_filename = key_filename

    def close(self):
        """A no-op stub method."""
        self.close_ += 1

    def exec_command(self, cmd, *args, **kwargs):
        return (
            self.ret_code,
            MockStdout(cmd, self.ret_code),
            MockStdout('', self.ret_code)
        )


class SSHTestCase(TestCase):
    """Tests for module ``robottelo.ssh``."""
    @mock.patch('robottelo.ssh.settings')
    def test_get_connection_key(self, settings):
        """Test method ``get_connection`` using key file to connect to the
        server.

        Mock up ``paramiko.SSHClient`` (by overriding method
        ``_call_paramiko_sshclient``) before calling ``get_connection``.
        Assert that certain parameters are passed to the (mock)
        ``paramiko.SSHClient`` object, and that certain methods on that object
        are called.
        """
        ssh._call_paramiko_sshclient = MockSSHClient  # pylint:disable=W0212

        key_filename = os.path.join(
            os.path.abspath(__name__), 'data', 'test_dsa.key'
        )
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = key_filename
        settings.ssh_client.command_timeout = 300
        settings.ssh_client.connection_timeout = 10
        with ssh.get_connection() as connection:  # pylint:disable=W0212
            self.assertEqual(connection.set_missing_host_key_policy_, 1)
            self.assertEqual(connection.connect_, 1)
            self.assertEqual(connection.close_, 0)
            self.assertEqual(connection.hostname, 'example.com')
            self.assertEqual(connection.username, 'nobody')
            self.assertEqual(connection.key_filename, key_filename)
        self.assertEqual(connection.set_missing_host_key_policy_, 1)
        self.assertEqual(connection.connect_, 1)
        self.assertEqual(connection.close_, 1)

    @mock.patch('robottelo.ssh.settings')
    def test_get_connection_pass(self, settings):
        """Test method ``get_connection`` using password of user to connect to
        the server

        Mock up ``paramiko.SSHClient`` (by overriding method
        ``_call_paramiko_sshclient``) before calling ``get_connection``.
        Assert that certain parameters are passed to the (mock)
        ``paramiko.SSHClient`` object, and that certain methods on that object
        are called.
        """
        ssh._call_paramiko_sshclient = MockSSHClient  # pylint:disable=W0212
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.ssh_client.command_timeout = 300
        settings.ssh_client.connection_timeout = 10
        with ssh.get_connection() as connection:  # pylint:disable=W0212
            self.assertEqual(connection.set_missing_host_key_policy_, 1)
            self.assertEqual(connection.connect_, 1)
            self.assertEqual(connection.close_, 0)
            self.assertEqual(connection.hostname, 'example.com')
            self.assertEqual(connection.username, 'nobody')
            self.assertEqual(connection.password, 'test_password')
        self.assertEqual(connection.set_missing_host_key_policy_, 1)
        self.assertEqual(connection.connect_, 1)
        self.assertEqual(connection.close_, 1)

    def test_valid_ssh_pub_keys(self):
        valid_keys = (
            ("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDuMCPmX7iBXAxH5oLznswA5cc"
             "fV/FABwIWnYl0OYRkDhv3mu9Eogk4H6sCguq4deJtRkwg2C3yEmsNYfBWYu4y5Rk"
             "I4TH/k3N161wn91nBxs/+wqoN3g9tUuWrf98PG4NnYvmZU67RuiSUNXpgLEPfo8j"
             "MKkJ5veKu++DmHdpfqFB9ljWEfWz+kAAKgwo251VRDaKwFsb91LbLFpqn9rfMJUB"
             "hOn+Uebfd0TrHzw08gbVmvfAn61isvFVhvIJBTjNSWsBIm8SuCvhH+inYOwttfE8"
             "FGeR1KSp9Xl0PCYDK0BwvQO3qwD+nehsEUR/FJUXm1IZPc8fi17ieGgPOnrgf"
             " user@new-host"),
            ("ssh-dss AAAAB3NzaC1kc3MAAACBAMzXU0Jl0fRCKy5B7R8KVKMLJYuhVPagBSi7"
             "UxRAiVHOHzscQzt5wrgRqknuQ9/xIAVAMUVy3ND5zBLkqKwGm9DKGeYEv7xxDi6Z"
             "z5QjsI9oSSqFSMauDxgl+foC4QPrIlUvb9ez5bVg6aJHKJEngDo+lvfVROgQOvTx"
             "I9IXn7oLAAAAFQCz4jDBOnTjkWXgw8sT46HM1jK4SwAAAIAS2BvUlEevY+2YOiqD"
             "SRy9Dhr+/bWLuLl7oUTEnxPhCyo8paaU0fJO1w3BUsbO3Rg4sBgXChRNyg7iKriB"
             "WbPH6EK1e6IcYv8wUdobB3wg+RJlYU2cq7V8HcPJh+hfAGfMD6UnTDLg+P5SCEW7"
             "Ag+knZNwfKv9IAtd0W86EFdVWwAAAIEAkj5boIRqLiUGbRipEzWzZbWMis2S8Ji2"
             "oR6fUD/h6bZ5ta8nEWApri5OQExK7upelTjSR+MHEDRmeepchkTX0LOjBkZgsPyb"
             "6nEpQUQUJAuns8yAnhsKuEuZmlAGwXOSKiD/KRyJu4KjbbV4oyKXU1fF70zPLmOT"
             "fyvserP5qyo= user@new-host"),
            ("ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAy"
             "NTYAAABBBPWuLEsYvplkL6XR5wbxzXyzw8tLE/JjLXlzUgxv4LhJN4iufXLPSOvj"
             "sk0ek1TE059poyy5ps+GU2DkisSUVYA= user@new-host")
        )
        for key in valid_keys:
            self.assertTrue(ssh.is_ssh_pub_key(key))

    def test_invalid_ssh_pub_keys(self):
        invalid_keys = (
            "ssh-rsa1 xxxxxx user@host",  # rsa1 is unsafe
            "foo bar blaz",  # not a valid type
            "ssh-rsa /gfdgdf/fsdfsdfsdf/@ user@host",  # not valid base64 data
            "sdhsfbghjsbgjhbg user@host",  # not a valid format
        )
        for key in invalid_keys:
            self.assertFalse(ssh.is_ssh_pub_key(key))

    def test_add_authorized_key_raises_invalid_key(self):
        with self.assertRaises(AttributeError):
            ssh.add_authorized_key('sfsdfsdfsdf')
        with self.assertRaises(AttributeError):
            ssh.add_authorized_key('sdhsfbghjsbgjhbg user@host')
        with self.assertRaises(AttributeError):
            ssh.add_authorized_key('ssh-rsa /gfdgdf/fsdfsdfsdf/@ user@host')

    def test_fails_with_invalid_key_format(self):
        with self.assertRaises(ValueError):
            ssh.add_authorized_key([])
        with self.assertRaises(ValueError):
            ssh.add_authorized_key(123456)
        with self.assertRaises(ValueError):
            ssh.add_authorized_key(9999.456789)
        with self.assertRaises(ValueError):
            ssh.add_authorized_key({"invalid": "format"})

    @mock.patch('robottelo.ssh.settings')
    def test_add_authorized_key(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient  # pylint:disable=W0212
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.ssh_client.command_timeout = 300
        settings.ssh_client.connection_timeout = 10
        ssh.add_authorized_key('ssh-rsa xxxx user@host')

    @mock.patch('robottelo.ssh.settings')
    def test_execute_command(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient  # pylint:disable=W0212
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.ssh_client.command_timeout = 300
        settings.ssh_client.connection_timeout = 10

        with ssh.get_connection() as connection:  # pylint:disable=W0212
            ret = ssh.execute_command('ls -la', connection)
            self.assertEqual(ret.stdout, [u'ls -la'])
            self.assertIsInstance(ret, ssh.SSHCommandResult)

    @mock.patch('robottelo.ssh.settings')
    def test_execute_command_plain_output(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient  # pylint:disable=W0212
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.ssh_client.command_timeout = 300
        settings.ssh_client.connection_timeout = 10

        with ssh.get_connection() as connection:  # pylint:disable=W0212
            ret = ssh.execute_command(
                'ls -la', connection, output_format='plain')
            self.assertEqual(ret.stdout, u'ls -la')
            self.assertIsInstance(ret, ssh.SSHCommandResult)

    @mock.patch('robottelo.ssh.settings')
    def test_command(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient  # pylint:disable=W0212
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.ssh_client.command_timeout = 300
        settings.ssh_client.connection_timeout = 10

        ret = ssh.command('ls -la')
        self.assertEqual(ret.stdout, [u'ls -la'])
        self.assertIsInstance(ret, ssh.SSHCommandResult)

    @mock.patch('robottelo.ssh.settings')
    def test_command_plain_output(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient  # pylint:disable=W0212
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.ssh_client.command_timeout = 300
        settings.ssh_client.connection_timeout = 10

        ret = ssh.command('ls -la', output_format='plain')
        self.assertEqual(ret.stdout, u'ls -la')
        self.assertIsInstance(ret, ssh.SSHCommandResult)

    @mock.patch('robottelo.ssh.settings')
    def test_parse_csv(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient  # pylint:disable=W0212
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.ssh_client.command_timeout = 300
        settings.ssh_client.connection_timeout = 10

        ret = ssh.command('a,b,c\n1,2,3', output_format='csv')
        self.assertEqual(ret.stdout, [{u'a': u'1', u'b': u'2', u'c': u'3'}])
        self.assertIsInstance(ret, ssh.SSHCommandResult)

    @mock.patch('robottelo.ssh.settings')
    def test_parse_json(self, settings):
        ssh._call_paramiko_sshclient = MockSSHClient  # pylint:disable=W0212
        settings.server.hostname = 'example.com'
        settings.server.ssh_username = 'nobody'
        settings.server.ssh_key = None
        settings.server.ssh_password = 'test_password'
        settings.ssh_client.command_timeout = 300
        settings.ssh_client.connection_timeout = 10

        ret = ssh.command('{"a": 1, "b": true}', output_format='json')
        self.assertEqual(ret.stdout, {u'a': u'1', u'b': True})
        self.assertIsInstance(ret, ssh.SSHCommandResult)

    def test_call_paramiko_client(self):
        self.assertIsInstance(
            ssh._call_paramiko_sshclient(),
            (paramiko.SSHClient, MockSSHClient)
        )
