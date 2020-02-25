import operator

import six
from unittest2 import TestCase

from robottelo import host_info
from robottelo.ssh import SSHCommandResult

if six.PY2:
    import mock
    from mock.mock import call
else:
    from unittest import mock
    from unittest.mock import call


class GetHostOsVersionTestCase(TestCase):
    """Tests for get_host_os_version version"""

    def setUp(self):
        """Mocking ssh"""
        self._patcher = mock.patch('robottelo.host_info.ssh.command')
        self._command = self._patcher.start()

    def tearDown(self):
        """Stop mock created on setUp method"""
        self._patcher.stop()

    def assert_rhel_version(self, ssh_version, parsed_version):
        """Encapsulate assertion logic regarding host os parsing

        :param ssh_version: version returned from ssh
        :param parsed_version: parsed version
        """
        self._command.return_value.stdout = [ssh_version]
        self.assertEqual(parsed_version, host_info.get_host_os_version.__wrapped__())
        self._command.assert_called_once_with('cat /etc/redhat-release')

    def test_rhel_major_version_parsing(self):
        """Check if can parse major versions.

        Semantic version  example: 1.2.3
        1 is major
        2 is minor
        3 is patch
        """
        self.assert_rhel_version('Red Hat Enterprise Linux Server release 6 (Maipo)', 'RHEL6')

    def test_rhel_minor_version_parsing(self):
        """Check if can parse minor versions"""
        self.assert_rhel_version('Red Hat Enterprise Linux Server release 7.2 (Maipo)', 'RHEL7.2')

    def test_rhel_patch_version_parsing(self):
        """Check if can parse patch versions"""
        self.assert_rhel_version(
            'Red Hat Enterprise Linux Server release 7.2.1 (Maipo)', 'RHEL7.2.1'
        )

    def test_cache(self):
        """Check get_host_os_version() calls are cached"""
        self._command.return_value.stdout = [
            'Red Hat Enterprise Linux Server release 7.2.1 (Maipo)'
        ]
        self.assertEqual('RHEL7.2.1', host_info.get_host_os_version())
        self._command.assert_called_once_with('cat /etc/redhat-release')
        self._command.return_value.stdout = ['Doesnt matter because because its cached']
        self.assertEqual('RHEL7.2.1', host_info.get_host_os_version())
        # if called more than once cache didn't worked
        self._command.assert_called_once_with('cat /etc/redhat-release')

    @mock.patch('robottelo.host_info.LOGGER')
    def test_command_error(self, logger):
        """Check returns 'Not Available' on error
        """
        cmd = SSHCommandResult(
            stdout=[],
            stderr='bash: generate: command not found\n',
            return_code=127,
            output_format=None,
        )
        self._command.return_value = cmd

        os_version = host_info.get_host_os_version.__wrapped__()
        self.assertEqual('Not Available', os_version)
        self._command.assert_called_once_with('cat /etc/redhat-release')
        logger.warning.assert_called_once_with('Host version not available: %r' % cmd)

    @mock.patch('robottelo.host_info.LOGGER')
    def test_command_parsing_error(self, logger):
        """Test return not available on Fedora machines
        It can be changed to handle other OS if needed
        """
        cmd = SSHCommandResult(stdout=['Fedora release 23 (Twenty Three)'], return_code=0)
        self._command.return_value = cmd
        os_version = host_info.get_host_os_version.__wrapped__()
        self.assertEqual('Not Available', os_version)
        self._command.assert_called_once_with('cat /etc/redhat-release')
        logger.warning.assert_called_once_with('Host version not available: %r' % cmd)


class GetHostSatVersionTestCase(TestCase):
    """Tests for get_host_sat_version version"""

    SSH_RESULT_ERROR = SSHCommandResult(
        stdout=[],
        stderr=('grep: /usr/share/foreman/lib/satellite/version.rb: No such file or directory'),
        return_code=127,
        output_format=None,
    )

    def setUp(self):
        """Mocking ssh"""
        self._patcher = mock.patch('robottelo.host_info.ssh.command')
        self._command = self._patcher.start()

    def tearDown(self):
        """Stop mock created on setUp method"""
        self._patcher.stop()

    def assert_sat_version(self, ssh_version, parsed_version):
        """Encapsulate assertion logic regarding host sat parsing

        :param ssh_version: version returned from ssh
        :param parsed_version: parsed version
        """
        self._command.return_value.stdout = [ssh_version]
        self.assertEqual(parsed_version, host_info.get_host_sat_version.__wrapped__())
        self._command.assert_called_once_with(host_info._SAT_6_2_VERSION_COMMAND)

    def test_sat_6_dot_2(self):
        """Check if can parse major 6.2.x versions"""
        self.assert_sat_version('satellite-6.2.0-21.1.el7sat.noarch', '6.2')

    def test_sat_6_dot_1(self):
        """Check if can parse major 6.2.x versions"""
        ssh_result_success = mock.Mock()
        ssh_result_success.return_code = 0
        ssh_result_success.stdout = ['  VERSION = "6.1.8"']

        self._command.side_effect = (self.SSH_RESULT_ERROR, ssh_result_success)
        sat_version = host_info.get_host_sat_version.__wrapped__()

        self.assertEqual("6.1", sat_version)
        calls = [
            call(host_info._SAT_6_2_VERSION_COMMAND),
            call(host_info._SAT_6_1_VERSION_COMMAND),
        ]
        self._command.assert_has_calls(calls)

    def test_cache(self):
        """Check get_host_sat_version() calls are cached"""
        self._command.return_value.stdout = ['  SATELLITE_SHORT_VERSION = "6.2"']
        self.assertEqual('6.2', host_info.get_host_sat_version())
        self._command.assert_called_once_with(host_info._SAT_6_2_VERSION_COMMAND)
        self._command.return_value.stdout = ['Doesnt matter because because its cached']
        self.assertEqual('6.2', host_info.get_host_sat_version())
        # if called more than once cache didn't worked
        self._command.assert_called_once_with(host_info._SAT_6_2_VERSION_COMMAND)

    @mock.patch('robottelo.host_info.LOGGER')
    def test_command_error(self, logger):
        """Check returns 'Not Available' on error
        """
        self._command.return_value = self.SSH_RESULT_ERROR

        sat_version = host_info.get_host_sat_version.__wrapped__()
        self.assertEqual('Not Available', sat_version)
        calls = [
            call(host_info._SAT_6_2_VERSION_COMMAND),
            call(host_info._SAT_6_1_VERSION_COMMAND),
        ]
        self._command.assert_has_calls(calls)
        logger.warning.assert_called_once_with(
            'Host Satellite version not available: %r' % self.SSH_RESULT_ERROR
        )


class SatVersionDependentValuesTestCase(TestCase):
    """Tests for SatVersionDependentValues class"""

    def setUp(self):
        """Set up version dependent values for all test"""
        self.dct_6_1 = {'id': 'rhel-7-server-satellite-tools-6.1-rpms'}
        self.dct_6_2 = {'id': 'rhel-7-server-satellite-tools-6.2-rpms'}
        self.sat_dep_values = host_info.SatVersionDependentValues(
            {"6.1": self.dct_6_1}, {"6.2": self.dct_6_2}
        )

    @mock.patch("robottelo.host_info.get_host_sat_version")
    def test_init(self, get_host_sat_version):
        """Test __init__ and check the is no call to get os Satellite version
        """
        self.assertEqual(
            {"6.1": self.dct_6_1, "6.2": self.dct_6_2}, self.sat_dep_values._versioned_values
        )
        self.assertFalse(get_host_sat_version.called)

    @mock.patch("robottelo.host_info.get_host_sat_version")
    def test_getitem(self, get_host_sat_version):
        """Check __getitem__ returns values dependent on Satellite version"""
        get_host_sat_version.return_value = '6.1'
        self.assertEqual(self.dct_6_1['id'], self.sat_dep_values['id'])
        self.assertTrue(get_host_sat_version.called)

        get_host_sat_version.return_value = '6.2'
        self.assertEqual(self.dct_6_2['id'], self.sat_dep_values['id'])


class SatVersionDepCommonValuesTestCase(SatVersionDependentValuesTestCase):
    """Tests for SatVersionDependentValues class common values"""

    def setUp(self):
        """Setup sat_version_dependent with common dict"""
        super(SatVersionDepCommonValuesTestCase, self).setUp()
        self.common = {}
        self.sat_dep_values = host_info.SatVersionDependentValues(
            {"6.1": self.dct_6_1}, {"6.2": self.dct_6_2}, common=self.common
        )

    def assert_missing(self):
        """ Check common missing is handled by common dct"""
        self.assertRaises(KeyError, operator.getitem, self.sat_dep_values, 'missing')
        self.common['missing'] = 'fallback'
        self.assertEqual('fallback', self.sat_dep_values['missing'])
        self.common.pop('missing')

    @mock.patch("robottelo.host_info.get_host_sat_version")
    def test_common_dct(self, get_host_sat_version):
        """Check common dct handle missing keys"""

        get_host_sat_version.return_value = '6.1'
        self.assertEqual(self.dct_6_1['id'], self.sat_dep_values['id'])
        self.assertTrue(get_host_sat_version.called)
        self.assert_missing()

        get_host_sat_version.return_value = '6.2'
        self.assertEqual(self.dct_6_2['id'], self.sat_dep_values['id'])
        self.assert_missing()

    @mock.patch("robottelo.host_info.get_host_sat_version")
    def test_common_dct_override(self, get_host_sat_version):
        """Check common is overridden by version dct """
        get_host_sat_version.return_value = '6.1'
        self.common['missing'] = 'fallback'
        self.assertEqual('fallback', self.sat_dep_values['missing'])
        self.dct_6_1['missing'] = 'override'
        self.assertEqual('override', self.sat_dep_values['missing'])
        self.dct_6_1.pop('missing')
        self.assertEqual('fallback', self.sat_dep_values['missing'])
