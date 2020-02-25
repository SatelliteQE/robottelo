"""Tests for module ``robottelo.decorators.host``."""
from itertools import chain

import six
import unittest2
from unittest2 import TestCase

from robottelo.decorators import host

if six.PY2:
    import mock
else:
    from unittest import mock


class SkipIfOSIsUnavailableTestCase(TestCase):
    """Tests for :func:`robottelo.decorators.host.skip_if_host_is` when host
    version isn't available
    """

    @classmethod
    def setUpClass(cls):
        """Setup versions above and bellow version 7.1

        Mocking setting so robottello.properties is not need to run this test
        Mocking get_host_os_version to define host version to 'Not Available'
        so it emulates an error when trying to fetch it through ssh
        """
        down_versions = '6 6.1 6.1.1'.split()
        up_versions = '7.1.1 7.2 7.2.1'.split()
        cls._up_and_down_versions = tuple('RHEL' + v for v in chain(down_versions, up_versions))
        cls._get_host_os_patcher = mock.patch('robottelo.decorators.host.get_host_os_version')
        cls._get_host_mock = cls._get_host_os_patcher.start()
        cls._get_host_mock.return_value = 'Not Available'
        cls._settings_patcher = mock.patch('robottelo.decorators.host.settings')
        cls._settings_patcher.start()

    def assert_not_skipped(self, dummy):
        """Assert a dummy function is not skipped"""
        try:
            self.assertTrue(dummy())
        except unittest2.SkipTest:
            self.fail('Should not be skipped')

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

            self.assert_not_skipped(dummy)

    def test_dont_skipping_with_multiple_versions(self):
        """Check don't skip if os version isn't available with multiple
        versions
        """

        @host.skip_if_os(*self._up_and_down_versions)
        def dummy():
            return True

        self.assert_not_skipped(dummy)


class SkipIfOSTestCase(SkipIfOSIsUnavailableTestCase):
    """Tests for :func:`robottelo.decorators.host.skip_if_host_is` when host
    version is available and equals to 'RHEL7.1'
    """

    @classmethod
    def setUpClass(cls):
        """Mocking dependencies just like superclass, but set host version to
        RHEL7.1.0
        """
        super(SkipIfOSTestCase, cls).setUpClass()
        cls._host_version = 'RHEL7.1.0'
        cls._get_host_mock.return_value = cls._host_version

    def test_skipping_with_patch_version(self):
        """Test skipping when decorator param is exactly equals to host
        version
        """

        @host.skip_if_os(self._host_version)
        def dummy():
            return True

        self.assertRaises(unittest2.SkipTest, dummy)

    def test_skipping_with_single_minor_version(self):
        """Test skipping when decorator param is equals to host version but
        omits patch
        """

        @host.skip_if_os('RHEL7.1')
        def dummy():
            return True

        self.assertRaises(unittest2.SkipTest, dummy)

    def test_skipping_with_single_major_version(self):
        """Test skipping when decorator param is equals to host version but
        omits minor and patch
        """

        @host.skip_if_os('RHEL7')
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
            'rhel',
            'Rhel',
            'rHel',
            'RHel',
            'rhEl',
            'RhEl',
            'rHEl',
            'RHEl',
            'rheL',
            'RheL',
            'rHeL',
            'RHeL',
            'rhEL',
            'RhEL',
            'rHEL',
            'RHEL',
        )
        for v in (p + '7.1.0' for p in all_cases):

            @host.skip_if_os(v)
            def dummy():
                return True

            self.assertRaises(unittest2.SkipTest, dummy)
