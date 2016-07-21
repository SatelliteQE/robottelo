"""Tests for module ``robottelo.decorators.host``."""
from itertools import chain

import six
import unittest2
from unittest2 import TestCase

from robottelo.decorators import host
from robottelo.ssh import SSHCommandResult

if six.PY2:
    import mock
else:
    from unittest import mock


class GetHostOsVersionTestCase(TestCase):
    """Tests for _get_host_os_version version"""

    def setUp(self):
        """Mocking ssh"""
        self._patcher = mock.patch(
            'robottelo.decorators.host.ssh.command')
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
        self.assertEqual(
            parsed_version,
            host._get_host_os_version.__wrapped__()
        )
        self._command.assert_called_once_with('cat /etc/redhat-release')

    def test_rhel_major_version_parsing(self):
        """Check if can parse major versions.

        Semantic version  example: 1.2.3
        1 is major
        2 is minor
        3 is patch
        """
        self.assert_rhel_version(
            u'Red Hat Enterprise Linux Server release 6 (Maipo)',
            u'RHEL6'
        )

    def test_rhel_minor_version_parsing(self):
        """Check if can parse minor versions"""
        self.assert_rhel_version(
            u'Red Hat Enterprise Linux Server release 7.2 (Maipo)',
            u'RHEL7.2'
        )

    def test_rhel_patch_version_parsing(self):
        """Check if can parse patch versions"""
        self.assert_rhel_version(
            u'Red Hat Enterprise Linux Server release 7.2.1 (Maipo)',
            u'RHEL7.2.1'
        )

    def test_cache(self):
        """Check _get_host_os_version() calls are cached"""
        self._command.return_value.stdout = [
            u'Red Hat Enterprise Linux Server release 7.2.1 (Maipo)'
        ]
        self.assertEqual(u'RHEL7.2.1', host._get_host_os_version())
        self._command.assert_called_once_with('cat /etc/redhat-release')
        self._command.return_value.stdout = [
            u'Doesnt matter because because its cached'
        ]
        self.assertEqual(u'RHEL7.2.1', host._get_host_os_version())
        # if called more than once cache didn't worked
        self._command.assert_called_once_with('cat /etc/redhat-release')

    @mock.patch('robottelo.decorators.host.LOGGER')
    def test_command_error(self, logger):
        """Check returns 'Not Available' on error
        """
        cmd = SSHCommandResult(
            stdout=[],
            stderr=u'bash: generate: command not found\n',
            return_code=127, output_format=None
        )
        self._command.return_value = cmd

        os_version = host._get_host_os_version.__wrapped__()
        self.assertEqual('Not Available', os_version)
        self._command.assert_called_once_with('cat /etc/redhat-release')
        logger.warning.assert_called_once_with(
            u'Host version not available: %r' % cmd)

    @mock.patch('robottelo.decorators.host.LOGGER')
    def test_command_parsing_error(self, logger):
        """Test return not available on Fedora machines
        It can be changed to handle other OS if needed
        """
        cmd = SSHCommandResult(
            stdout=[u'Fedora release 23 (Twenty Three)'],
            return_code=0
        )
        self._command.return_value = cmd
        os_version = host._get_host_os_version.__wrapped__()
        self.assertEqual('Not Available', os_version)
        self._command.assert_called_once_with('cat /etc/redhat-release')
        logger.warning.assert_called_once_with(
            u'Host version not available: %r' % cmd
        )


class SkipIfOSIsUnavailableTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.host.skip_if_host_is` when host
    version isn't available
    """

    @classmethod
    def setUpClass(cls):
        """Setup versions above and bellow version 7.1

        Mocking setting so robottello.properties is not need to run this test
        Mocking _get_host_os_version to define host version to 'Not Available'
        so it emulates an error when trying to fetch it through ssh
        """
        down_versions = u'6 6.1 6.1.1 7 7.0'.split()
        up_versions = u'7.1.1 7.2 7.2.1 8'.split()
        cls._up_and_down_versions = tuple(
            u'RHEL' + v for v in chain(down_versions, up_versions)
        )
        cls._get_host_os_patcher = mock.patch(
            'robottelo.decorators.host._get_host_os_version'
        )
        cls._get_host_mock = cls._get_host_os_patcher.start()
        cls._get_host_mock.return_value = 'Not Available'
        cls._settings_patcher = mock.patch(
            'robottelo.decorators.host.settings'
        )
        cls._settings_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls._get_host_os_patcher.stop()
        cls._settings_patcher.stop()

    def test_dont_skipping_with_single_version(self):
        """Check don't skip if os version isn't available"""
        for single_version in self._up_and_down_versions:
            @host.skip_if_os(single_version)
            def dummy():
                return True

            self.assertTrue(dummy())

    def test_dont_skipping_with_multiple_versions(self):
        """Check don't skip if os version isn't available with multiple
        versions
        """

        @host.skip_if_os(*self._up_and_down_versions)
        def dummy():
            return True

        self.assertTrue(dummy())


class SkipIfOSTestCase(SkipIfOSIsUnavailableTestCase):
    """Tests for :func:`robottelo.decorators.host.skip_if_host_is` when host
    version is available and equals to u'RHEL7.1'
    """

    @classmethod
    def setUpClass(cls):
        """Mocking depencies just like superclass, but set host version to 7.1
        """
        super(SkipIfOSTestCase, cls).setUpClass()
        cls._host_version = u'RHEL7.1'
        cls._get_host_mock.return_value = cls._host_version

    def test_skipping_with_single_version(self):
        """Test skipping when decorator params is equals to host version"""

        @host.skip_if_os(self._host_version)
        def dummy():
            return True

        self.assertRaises(unittest2.SkipTest, dummy)

    def test_skipping_with_multiple_versions(self):
        """Test skipping when decorator params contains host version"""
        versions = self._up_and_down_versions + (self._host_version,)

        @host.skip_if_os(*versions)
        def dummy():
            return True

        self.assertRaises(unittest2.SkipTest, dummy)

    def test_skipping_non_normalized_version(self):
        """Test skipping occurs even if version prefix is not normalized"""
        all_cases = (
            'rhel', 'Rhel', 'rHel', 'RHel', 'rhEl', 'RhEl', 'rHEl', 'RHEl',
            'rheL', 'RheL', 'rHeL', 'RHeL', 'rhEL', 'RhEL', 'rHEL', 'RHEL'
        )
        for v in (p + '7.1' for p in all_cases):
            @host.skip_if_os(v)
            def dummy():
                return True

            self.assertRaises(unittest2.SkipTest, dummy)
