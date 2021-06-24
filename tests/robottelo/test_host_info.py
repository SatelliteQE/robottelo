from unittest import mock
from unittest.mock import call

import pytest
from attrdict import AttrDict

from robottelo import host_info
from robottelo.ssh import SSHCommandResult


class TestGetHostOsVersion:
    """Tests for get_host_os_version version"""

    @pytest.fixture(scope="function")
    def ssh_result(self):
        """Mocking ssh"""
        patcher = mock.patch('robottelo.host_info.ssh.command')
        yield patcher.start()

        host_info.get_host_os_version.cache_clear()
        patcher.stop()

    def assert_rhel_version(self, ssh_version, parsed_version, ssh_result):
        """Encapsulate assertion logic regarding host os parsing

        :param ssh_version: version returned from ssh
        :param parsed_version: parsed version
        """
        ssh_result.return_value.stdout = [ssh_version]
        assert parsed_version == host_info.get_host_os_version.__wrapped__()
        ssh_result.assert_called_once_with('cat /etc/redhat-release')

    def test_rhel_major_version_parsing(self, ssh_result):
        """Check if can parse major versions.

        Semantic version  example: 1.2.3
        1 is major
        2 is minor
        3 is patch
        """
        self.assert_rhel_version(
            'Red Hat Enterprise Linux Server release 6 (Maipo)', 'RHEL6', ssh_result
        )

    def test_rhel_minor_version_parsing(self, ssh_result):
        """Check if can parse minor versions"""
        self.assert_rhel_version(
            'Red Hat Enterprise Linux Server release 7.2 (Maipo)', 'RHEL7.2', ssh_result
        )

    def test_rhel_patch_version_parsing(self, ssh_result):
        """Check if can parse patch versions"""
        self.assert_rhel_version(
            'Red Hat Enterprise Linux Server release 7.2.1 (Maipo)', 'RHEL7.2.1', ssh_result
        )

    def test_cache(self, request, ssh_result):
        """Check get_host_os_version() calls are cached"""
        ssh_result.return_value.stdout = ['Red Hat Enterprise Linux Server release 7.2.1 (Maipo)']
        assert 'RHEL7.2.1' == host_info.get_host_os_version()
        ssh_result.assert_called_once_with('cat /etc/redhat-release')
        ssh_result.return_value.stdout = ['Doesnt matter because because its cached']
        assert 'RHEL7.2.1' == host_info.get_host_os_version()
        # if called more than once cache didn't worked
        ssh_result.assert_called_once_with('cat /etc/redhat-release')

    @mock.patch('robottelo.host_info.logger')
    def test_command_error(self, logger, ssh_result):
        """Check returns 'Not Available' on error"""
        cmd = SSHCommandResult(
            stdout=[],
            stderr='bash: generate: command not found\n',
            return_code=127,
            output_format=None,
        )
        ssh_result.return_value = cmd

        os_version = host_info.get_host_os_version.__wrapped__()
        assert 'Not Available' == os_version
        ssh_result.assert_called_once_with('cat /etc/redhat-release')
        logger.warning.assert_called_once_with('Host version not available: %r' % cmd)

    @mock.patch('robottelo.host_info.logger')
    def test_command_parsing_error(self, logger, ssh_result):
        """Test return not available on Fedora machines
        It can be changed to handle other OS if needed
        """
        cmd = SSHCommandResult(stdout=['Fedora release 23 (Twenty Three)'], return_code=0)
        ssh_result.return_value = cmd
        os_version = host_info.get_host_os_version.__wrapped__()
        assert 'Not Available' == os_version
        ssh_result.assert_called_once_with('cat /etc/redhat-release')
        logger.warning.assert_called_once_with('Host version not available: %r' % cmd)


class TestGetHostSatVersion:
    """Tests for get_host_sat_version version"""

    SSH_RESULT_ERROR = SSHCommandResult(
        stdout=[],
        stderr=('grep: /usr/share/foreman/lib/satellite/version.rb: No such file or directory'),
        return_code=127,
        output_format=None,
    )

    @pytest.fixture(scope="function")
    def ssh_result(self):
        """Mocking ssh"""
        patcher = mock.patch('robottelo.host_info.ssh.command')
        yield patcher.start()

        host_info.get_host_sat_version.cache_clear()
        patcher.stop()

    def test_sat_6_dot_2(self, ssh_result):
        """Check if can parse major 6.2.x versions"""
        ssh_result.return_value.stdout = ['satellite-6.2.0-21.1.el7sat.noarch']
        assert '6.2' == host_info.get_host_sat_version.__wrapped__()
        ssh_result.assert_called_once_with(host_info._SAT_6_2_VERSION_COMMAND)

    def test_sat_6_dot_1(self, ssh_result):
        """Check if can parse major 6.2.x versions"""
        ssh_result_success = mock.Mock()
        ssh_result_success.return_code = 0
        ssh_result_success.stdout = ['  VERSION = "6.1.8"']

        ssh_result.side_effect = (self.SSH_RESULT_ERROR, ssh_result_success)
        sat_version = host_info.get_host_sat_version.__wrapped__()

        assert "6.1" == sat_version
        calls = [
            call(host_info._SAT_6_2_VERSION_COMMAND),
            call(host_info._SAT_6_1_VERSION_COMMAND),
        ]
        ssh_result.assert_has_calls(calls)

    def test_cache(self, ssh_result):
        """Check get_host_sat_version() calls are cached"""
        ssh_result.return_value.stdout = ['  SATELLITE_SHORT_VERSION = "6.2"']
        assert '6.2' == host_info.get_host_sat_version()
        ssh_result.assert_called_once_with(host_info._SAT_6_2_VERSION_COMMAND)
        ssh_result.return_value.stdout = ['Doesnt matter because because its cached']
        assert '6.2' == host_info.get_host_sat_version()
        # if called more than once cache didn't worked
        ssh_result.assert_called_once_with(host_info._SAT_6_2_VERSION_COMMAND)

    @mock.patch('robottelo.host_info.logger')
    def test_command_error(self, logger, ssh_result):
        """Check returns 'Not Available' on error"""
        ssh_result.return_value = self.SSH_RESULT_ERROR

        sat_version = host_info.get_host_sat_version.__wrapped__()
        assert 'Not Available' == sat_version
        calls = [
            call(host_info._SAT_6_2_VERSION_COMMAND),
            call(host_info._SAT_6_1_VERSION_COMMAND),
        ]
        ssh_result.assert_has_calls(calls)
        logger.warning.assert_called_once_with(
            'Host Satellite version not available: %r' % self.SSH_RESULT_ERROR
        )


class TestSatVersionDependentValues:
    """Tests for SatVersionDependentValues class"""

    rpms_61 = {'id': 'rhel-7-server-satellite-tools-6.1-rpms'}
    rpms_62 = {'id': 'rhel-7-server-satellite-tools-6.2-rpms'}

    @pytest.fixture(scope="class")
    def dep_versions_data(self):
        """Set up version dependent values for all test"""

        versions = AttrDict(
            {
                'd_6_1': self.rpms_61,
                'd_6_2': self.rpms_62,
                'sat_dep_values': host_info.SatVersionDependentValues(
                    {"6.1": self.rpms_61}, {"6.2": self.rpms_62}
                ),
            }
        )
        yield versions

        host_info.get_host_sat_version.cache_clear()

    @mock.patch("robottelo.host_info.get_host_sat_version")
    def test_init(self, get_host_sat_version, dep_versions_data):
        """Test __init__ and check the is no call to get os Satellite version"""
        assert dep_versions_data.sat_dep_values._versioned_values == {
            "6.1": dep_versions_data.d_6_1,
            "6.2": dep_versions_data.d_6_2,
        }
        assert not get_host_sat_version.called

    @mock.patch("robottelo.host_info.get_host_sat_version")
    def test_getitem(self, get_host_sat_version, dep_versions_data):
        """Check __getitem__ returns values dependent on Satellite version"""
        get_host_sat_version.return_value = '6.1'
        assert dep_versions_data.d_6_1['id'] == dep_versions_data.sat_dep_values['id']
        assert get_host_sat_version.called

        get_host_sat_version.return_value = '6.2'
        assert dep_versions_data.d_6_2['id'] == dep_versions_data.sat_dep_values['id']

    @pytest.fixture(scope="function")
    def common_versions_data(self, dep_versions_data):
        dep_versions_data.common = {}
        dep_versions_data.sat_dep_values = host_info.SatVersionDependentValues(
            {"6.1": dep_versions_data.d_6_1}, {"6.2": dep_versions_data.d_6_2}, common={}
        )
        return dep_versions_data

    @mock.patch("robottelo.host_info.get_host_sat_version")
    def test_common_dct(self, get_host_sat_version, common_versions_data):
        """Check common dct handle missing keys"""
        get_host_sat_version.return_value = '6.1'
        assert common_versions_data.d_6_1['id'] == common_versions_data.sat_dep_values['id']
        assert get_host_sat_version.called

        get_host_sat_version.return_value = '6.2'
        assert common_versions_data.d_6_2['id'] == common_versions_data.sat_dep_values['id']

        with pytest.raises(KeyError):
            common_versions_data.sat_dep_values['missing_version']
        common_versions_data.sat_dep_values = host_info.SatVersionDependentValues(
            common={'missing_version': 'fallback'}
        )
        # no keyerror with it added to common
        assert 'fallback' == common_versions_data.sat_dep_values['missing_version']

    @mock.patch("robottelo.host_info.get_host_sat_version")
    def test_common_dct_override(self, get_host_sat_version, common_versions_data):
        """Check common is overridden by version dct"""
        get_host_sat_version.return_value = '6.1'
        common_versions_data.sat_dep_values = host_info.SatVersionDependentValues(
            {"6.1": self.rpms_61}, {"6.2": self.rpms_62}, common={'missing_version': 'fallback'}
        )
        assert 'fallback' == common_versions_data.sat_dep_values['missing_version']
        common_versions_data.sat_dep_values = host_info.SatVersionDependentValues(
            {"6.1": {'missing_version': 'override'}}, common={'missing_version': 'fallback'}
        )
        assert 'override' == common_versions_data.sat_dep_values['missing_version']
        common_versions_data.sat_dep_values = host_info.SatVersionDependentValues(
            {"6.1": self.rpms_61}, common={'missing_version': 'fallback'}
        )
        assert 'fallback' == common_versions_data.sat_dep_values['missing_version']
