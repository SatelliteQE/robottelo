import six
import unittest2
from unittest2 import TestCase
from itertools import chain
from robottelo.decorators import host
from robottelo.ssh import SSHCommandResult

if six.PY2:
    import mock
else:
    from unittest import mock


class GetHostOsVersionTestCase(TestCase):
    def setUp(self):
        self._patcher = mock.patch(
            'robottelo.decorators.host.ssh.command')
        self._command = self._patcher.start()

    def tearDown(self):
        self._patcher.stop()

    def assert_rhel_version(self, ssh_version, parsed_version):
        self._command.return_value.stdout = [ssh_version]
        self.assertEqual(parsed_version, host._get_host_os_version())
        self._command.assert_called_once_with('cat /etc/redhat-release')

    def test_rhel_6(self):
        self.assert_rhel_version(
            u'Red Hat Enterprise Linux Server release 6 (Maipo)',
            u'RHEL6'
        )

    def test_rhel_7_2(self):
        self.assert_rhel_version(
            u'Red Hat Enterprise Linux Server release 7.2 (Maipo)',
            u'RHEL7.2'
        )

    def test_rhel_7_2_1(self):
        self.assert_rhel_version(
            u'Red Hat Enterprise Linux Server release 7.2.1 (Maipo)',
            u'RHEL7.2.1'
        )

    def test_cache(self):
        self._command.return_value.stdout = [
            u'Red Hat Enterprise Linux Server release 7.2.1 (Maipo)'
        ]
        self.assertEqual(u'RHEL7.2.1', host._cached_host_os_version())
        self._command.assert_called_once_with('cat /etc/redhat-release')
        self._command.return_value.stdout = [
            u'Doesnt matter because because its cached'
        ]
        self.assertEqual(u'RHEL7.2.1', host._cached_host_os_version())
        # if called more than once cache didn't worked
        self._command.assert_called_once_with('cat /etc/redhat-release')

    @mock.patch('robottelo.decorators.host.LOGGER')
    def test_command_error(self, logger):
        cmd = SSHCommandResult(
            stdout=[],
            stderr=u'bash: generate: command not found\n',
            return_code=127, output_format=None
        )
        self._command.return_value = cmd

        host._get_host_os_version()
        self._command.assert_called_once_with('cat /etc/redhat-release')
        logger.warning.assert_called_once_with(
            u'Host version not available: %r' % cmd)

    @mock.patch('robottelo.decorators.host.LOGGER')
    def test_command_parsing_error(self, logger):
        cmd = SSHCommandResult(
            stdout=[u'Fedora release 23 (Twenty Three)'],
            return_code=0
        )
        self._command.return_value = cmd

        host._get_host_os_version()
        self._command.assert_called_once_with('cat /etc/redhat-release')
        logger.warning.assert_called_once_with(
            u'Host version not available: %r' % cmd
        )


class SkipIfHostVersionIsUnavailableTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.host.skip_if_host_is` when host
    version isn't available
    """

    @classmethod
    def setUpClass(cls):
        down_versions = u'6 6.1 6.1.1 7 7.0'.split()
        up_versions = u'7.1.1 7.2 7.2.1 8'.split()
        cls._up_and_down_versions = tuple(
            u'RHEL' + v for v in chain(down_versions, up_versions)
        )
        cls._cache_patcher = mock.patch(
            'robottelo.decorators.host._cached_host_os_version'
        )
        cls._cached_function_mock = cls._cache_patcher.start()
        cls._cached_function_mock.return_value = 'Not Available'
        cls._settings_patcher = mock.patch(
            'robottelo.decorators.host.settings'
        )
        cls._settings_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls._cache_patcher.stop()
        cls._settings_patcher.stop()

    def test_negative_skipping_with_single_version(self):
        for single_version in self._up_and_down_versions:
            @host.skip_if_os(single_version)
            def dummy():
                return True

            self.assertTrue(dummy())

    def test_negative_skipping_with_multiple_versions(self):
        @host.skip_if_os(*self._up_and_down_versions)
        def dummy():
            return True

        self.assertTrue(dummy())


class SkipIfHostIsTestCase(SkipIfHostVersionIsUnavailableTestCase):
    """Tests for :func:`robottelo.decorators.host.skip_if_host_is`."""

    @classmethod
    def setUpClass(cls):
        super(SkipIfHostIsTestCase, cls).setUpClass()
        cls._host_version = u'RHEL7.1'
        cls._cached_function_mock.return_value = cls._host_version

    def test_positive_skipping_with_single_version(self):
        @host.skip_if_os(self._host_version)
        def dummy():
            return True

        self.assertRaises(unittest2.SkipTest, dummy)

    def test_positive_skipping_with_multiple_versions(self):
        versions = self._up_and_down_versions + (self._host_version,)

        @host.skip_if_os(*versions)
        def dummy():
            return True

        self.assertRaises(unittest2.SkipTest, dummy)

    def test_positive_skipping_non_normalized_version(self):
        all_cases = (
            'rhel', 'Rhel', 'rHel', 'RHel', 'rhEl', 'RhEl', 'rHEl', 'RHEl',
            'rheL', 'RheL', 'rHeL', 'RHeL', 'rhEL', 'RhEL', 'rHEL', 'RHEL'
        )
        for v in (p + '7.1' for p in all_cases):
            @host.skip_if_os(v)
            def dummy():
                return True

            self.assertRaises(unittest2.SkipTest, dummy)
