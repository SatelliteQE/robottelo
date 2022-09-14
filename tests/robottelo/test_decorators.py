"""Unit tests for :mod:`robottelo.utils.decorators`."""
from unittest import mock

import pytest

from robottelo.utils import decorators


class TestCacheable:
    """Tests for :func:`robottelo.utils.decorators.cacheable`."""

    @pytest.fixture(scope="function")
    def make_foo(self):
        mocked_object_cache_patcher = mock.patch.dict('robottelo.utils.decorators.OBJECT_CACHE')
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
