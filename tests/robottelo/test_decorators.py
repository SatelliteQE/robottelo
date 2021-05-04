"""Unit tests for :mod:`robottelo.decorators`."""
from itertools import chain
from unittest import mock

import pytest
from unittest2 import SkipTest

from robottelo import decorators


class TestCacheable:
    """Tests for :func:`robottelo.decorators.cacheable`."""

    @pytest.fixture(scope="function")
    def make_foo(self):
        mocked_object_cache_patcher = mock.patch.dict('robottelo.decorators.OBJECT_CACHE')
        mocked_object_cache_patcher.start()

        # decorators.cacheable uses the function name as the key, removing make_
        def make_foo(options):
            return {'id': 42}

        yield decorators.cacheable(make_foo)

        mocked_object_cache_patcher.stop()

    def test_create_and_not_add_to_cache(self, make_foo):
        """Create a new object and not add it to the cache.
        First test in the class, as the other tests add to the cache
        """
        make_foo(cached=False)
        assert 'foo' not in decorators.OBJECT_CACHE
        assert decorators.OBJECT_CACHE == {}

    def test_build_cache(self, make_foo):
        """Create a new object and add it to the cache."""
        obj = make_foo(cached=True)
        assert decorators.OBJECT_CACHE == {'foo': {'id': 42}}
        assert id(decorators.OBJECT_CACHE['foo']) == id(obj)

    def test_return_from_cache(self, make_foo):
        """Return an already cached object."""
        cache_obj = {'id': 42}
        decorators.OBJECT_CACHE['foo'] = cache_obj
        obj = make_foo(cached=True)
        assert id(cache_obj) == id(obj)


class TestHostSkipIf:
    """Tests for :func:`robottelo.decorators.host.skip_if_host_is` when host
    version isn't available
    """

    DOWN_VERSIONS = '6 6.1 6.1.1'.split()
    UP_VERSIONS = '7.1.1 7.2 7.2.1'.split()
    VERSIONS = tuple('RHEL' + v for v in chain(DOWN_VERSIONS, UP_VERSIONS))

    @pytest.fixture(scope="class")
    def settings_mock(self):
        settings_patch = mock.patch('robottelo.decorators.host.settings')
        mocker = settings_patch.start()

        yield mock
        mocker.stop()

    @pytest.fixture(scope="class")
    def version_unknown_mock(self, settings_mock):
        """Setup versions above and below version 7.1

        Mocking setting so robottello.properties is not need to run this test
        Mocking get_host_os_version to define host version to 'Not Available'
        so it emulates an error when trying to fetch it through ssh
        """
        host_os_patch = mock.patch('robottelo.decorators.host.get_host_os_version')
        host_os_mock = host_os_patch.start()
        host_os_mock.return_value = 'Not Available'

        yield host_os_mock
        host_os_mock.stop()

    def assert_not_skipped(self, dummy):
        """Assert a dummy function is not skipped"""
        try:
            assert dummy()
        except SkipTest:
            pytest.fail('Should not be skipped')

    @pytest.mark.parametrize('single_version', VERSIONS)
    def test_dont_skipping_with_single_version(self, version_unknown_mock, single_version):
        """Check don't skip if os version isn't available"""

        @decorators.host.skip_if_os(single_version)
        def dummy():
            return True

        self.assert_not_skipped(dummy)

    def test_dont_skipping_with_multiple_versions(self, version_unknown_mock):
        """Check don't skip if os version isn't available with multiple
        versions
        """

        @decorators.host.skip_if_os(*self.VERSIONS)
        def dummy():
            return True

        self.assert_not_skipped(dummy)

    @pytest.fixture(scope="class")
    def version_known_mock(self, version_unknown_mock):
        """Mocking dependencies just like superclass, but set host version to
        RHEL7.1.0

        Warning: mutates its ancestor fixture instance
        """
        version_unknown_mock._host_version = 'RHEL7.1.0'
        version_unknown_mock.return_value = version_unknown_mock._host_version

        return version_unknown_mock  # leave teardown to the ancestor

    def test_skipping_with_patch_version(self, version_known_mock):
        """Test skipping when decorator param is exactly equals to host
        version
        """

        @decorators.host.skip_if_os(version_known_mock._host_version)
        def dummy():
            return True

        with pytest.raises(SkipTest):
            dummy()

    def test_skipping_with_single_minor_version(self, version_known_mock):
        """Test skipping when decorator param is equals to host version but
        omits patch
        """

        @decorators.host.skip_if_os('RHEL7.1')
        def dummy():
            return True

        with pytest.raises(SkipTest):
            dummy()

    def test_skipping_with_single_major_version(self, version_known_mock):
        """Test skipping when decorator param is equals to host version but
        omits minor and patch
        """

        @decorators.host.skip_if_os('RHEL7')
        def dummy():
            return True

        with pytest.raises(SkipTest):
            dummy()

    def test_skipping_with_multiple_versions(self, version_known_mock):
        """Test skipping when decorator params contains host version"""
        versions = self.VERSIONS + (version_known_mock._host_version,)

        @decorators.host.skip_if_os(*versions)
        def dummy():
            return True

        with pytest.raises(SkipTest):
            dummy()

    @pytest.mark.parametrize(
        'version',
        [
            f'{v}7.1.0'
            for v in [
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
            ]
        ],
    )
    def test_skipping_non_normalized_version(self, version_known_mock, version):
        """Test skipping occurs even if version prefix is not normalized"""

        @decorators.host.skip_if_os(version)
        def dummy():
            return True

        with pytest.raises(SkipTest):
            dummy()
