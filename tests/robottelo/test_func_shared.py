import multiprocessing
import os
import time

import pytest
from fauxfactory import gen_integer
from fauxfactory import gen_string

from robottelo.utils.decorators.func_shared.file_storage import get_temp_dir
from robottelo.utils.decorators.func_shared.file_storage import TEMP_FUNC_SHARED_DIR
from robottelo.utils.decorators.func_shared.file_storage import TEMP_ROOT_DIR
from robottelo.utils.decorators.func_shared.shared import _NAMESPACE_SCOPE_KEY_TYPE
from robottelo.utils.decorators.func_shared.shared import _set_configured
from robottelo.utils.decorators.func_shared.shared import enable_shared_function
from robottelo.utils.decorators.func_shared.shared import set_default_scope
from robottelo.utils.decorators.func_shared.shared import shared
from robottelo.utils.decorators.func_shared.shared import SharedFunctionException

DEFAULT_POOL_SIZE = 8
SIMPLE_TIMEOUT_VALUE = 3

_this_module_name = 'tests.robottelo.test_func_shared'
_set_configured(True)


class MainCounter:
    """Basic class that contain a counter function"""

    class SubCounter:
        """Basic sub class that contain a counter function"""

        @classmethod
        @shared
        def shared_counter(cls, value=0, increment_by=1):
            """a basic counter function in a sub class"""
            return value + increment_by

    @classmethod
    @shared
    def shared_counter(cls, value=0, increment_by=1):
        """a basic counter function in a class"""
        return value + increment_by


@shared
def shared_counter(value=0, increment_by=1):
    """a basic counter function"""
    return value + increment_by


@shared(scope_context='shared_counter')
def shared_counter_with_scope_context(value=0, increment_by=1):
    """a basic counter function"""
    return value + increment_by


@shared
def simple_shared_counter_increment(index=1, increment_by=1):
    """a simple shared function each time called increment index"""
    return {'index': index + increment_by}


@shared
def simple_shared_counter_increment_process(index=1):
    """a simple shared function each time called increment index by a new
    generated value"""
    return {'index': index + gen_integer(min_value=1, max_value=100)}


@shared(timeout=SIMPLE_TIMEOUT_VALUE)
def simple_shared_counter_increment_timeout(index=1):
    """a simple shared function each time called increment index by one.

    note: this shared function sleep for 2 seconds, and have expire time 1
        second, as a result it should always return a new value
    """
    return {'index': index + 1}


@shared(timeout=SIMPLE_TIMEOUT_VALUE)
def simple_shared_counter_increment_process_timeout(index=1):
    """a simple shared function each time called increment index by one.

    note: this shared function sleep for 2 seconds, and have expire time 1
        second, as a result it should always return a new value
    """
    return {'index': index + 1}


@shared(inject=True, injected_kw='_injected')
def simple_shared_counter_with_inject(index=0, _injected=False):
    if _injected:
        index += 100
    else:
        index += 1

    return {'index': index}


@shared(inject=True, injected_kw='_injected')
def simple_shared_counter_with_inject_multiprocess(index=0, _injected=False):
    """The first caller will receive index+1, others index+1+100"""
    if _injected:
        index += 100
    else:
        index += 1

    return {'index': index}


@shared(inject=True, injected_kw=None)
def simple_shared_with_inject_kw_none(index=None):
    """To test kwargs injection without injected kw"""
    if index is None:
        index = 100
    else:
        index += 1000

    return {'index': index}


@shared
def simple_shared_counter_with_exception(index=0):
    """Raise division by 0 error"""
    index /= 0
    return {'index': index + 1}


@shared
def basic_shared_counter(index=0, increment_by=1):
    """used with use_shared_data=False"""
    return index + increment_by


@shared(function_kw=['prefix', 'suffix'])
def basic_shared_counter_string(prefix='', suffix='', counter=0, increment_by=1):
    """basic function that increment a counter and return a string with
    prefix
    """
    return f'{prefix}_{counter + increment_by}_{suffix}'


class NotRestorableException(Exception):
    """this exception is not restorable as need mote args"""

    def __init__(self, msg, details):
        self.msg = msg
        self.details = details


@shared
def simple_shared_counter_with_exception_not_restored(index=0):
    """Raise exception that should not be restorable"""
    raise NotRestorableException('error', 'I am not restorable')


class TestFuncShared:
    @pytest.fixture(scope='class')
    def scope(self):
        # generate a new namespace
        scope = gen_string('alpha', 10)
        set_default_scope(scope)
        yield scope

    @pytest.fixture(scope='function', autouse=True)
    def enable(self):
        enable_shared_function(True)

    @pytest.fixture(scope='function')
    def pool(self):
        pool = multiprocessing.Pool(DEFAULT_POOL_SIZE)
        yield pool

        pool.terminate()
        pool.join()

    def test_basic_without_using_shared_data(self):
        """Ensure that USE_SHARED_DATA is false. The function is called and does
        not use the cached data
        """
        enable_shared_function(False)

        value = gen_integer(min_value=1, max_value=10000)
        increment_by = gen_integer(min_value=1, max_value=10000)
        new_value = basic_shared_counter(index=value, increment_by=increment_by)
        assert new_value == value + increment_by

        second_new_value = basic_shared_counter(index=new_value, increment_by=increment_by)
        assert second_new_value == new_value + increment_by

    def test_shared_counter_file_path(self, scope):
        """Test file path when function is at module level"""
        expected_shared_file_path = os.path.join(
            get_temp_dir(),
            TEMP_ROOT_DIR,
            TEMP_FUNC_SHARED_DIR,
            '.'.join([scope, _NAMESPACE_SCOPE_KEY_TYPE, _this_module_name, 'shared_counter']),
        )
        assert not os.path.exists(expected_shared_file_path)

        value = gen_integer(min_value=1, max_value=10000)
        increment_by = gen_integer(min_value=1, max_value=10000)
        counter_value = shared_counter(value=value, increment_by=increment_by)
        assert counter_value == value + increment_by

        value_2 = gen_integer(min_value=1, max_value=10000)
        while value_2 == value:
            value_2 = gen_integer(min_value=1, max_value=10000)
        increment_by_2 = gen_integer(min_value=1, max_value=10000)
        while increment_by_2 == increment_by:
            increment_by_2 = gen_integer(min_value=1, max_value=10000)
        counter_value_shared = shared_counter(value=value_2, increment_by=increment_by_2)
        assert counter_value_shared == counter_value

        assert os.path.exists(expected_shared_file_path)

    def test_shared_counter_file_path_with_scope_context(self, scope):
        """Test file path when function is at module level"""
        expected_shared_file_path = os.path.join(
            get_temp_dir(),
            TEMP_ROOT_DIR,
            TEMP_FUNC_SHARED_DIR,
            '.'.join(
                [
                    scope,
                    _NAMESPACE_SCOPE_KEY_TYPE,
                    'shared_counter',
                    _this_module_name,
                    'shared_counter_with_scope_context',
                ]
            ),
        )
        assert not os.path.exists(expected_shared_file_path)
        value = gen_integer(min_value=1, max_value=10000)
        increment_by = gen_integer(min_value=1, max_value=10000)
        counter_value = shared_counter_with_scope_context(value=value, increment_by=increment_by)
        assert counter_value == value + increment_by

        value_2 = gen_integer(min_value=1, max_value=10000)
        while value_2 == value:
            value_2 = gen_integer(min_value=1, max_value=10000)
        increment_by_2 = gen_integer(min_value=1, max_value=10000)
        while increment_by_2 == increment_by:
            increment_by_2 = gen_integer(min_value=1, max_value=10000)
        counter_value_shared = shared_counter_with_scope_context(
            value=value_2, increment_by=increment_by_2
        )
        assert counter_value_shared == counter_value

        assert os.path.exists(expected_shared_file_path)

    def test_shared_main_counter_class_file_path(self, scope):
        """Test file path when function is in a class"""
        expected_shared_file_path = os.path.join(
            get_temp_dir(),
            TEMP_ROOT_DIR,
            TEMP_FUNC_SHARED_DIR,
            '.'.join(
                [
                    scope,
                    _NAMESPACE_SCOPE_KEY_TYPE,
                    _this_module_name,
                    'MainCounter.shared_counter',
                ]
            ),
        )
        assert not os.path.exists(expected_shared_file_path)
        value = gen_integer(min_value=1, max_value=10000)
        increment_by = gen_integer(min_value=1, max_value=10000)
        counter_value = MainCounter.shared_counter(value=value, increment_by=increment_by)
        assert counter_value == value + increment_by

        value_2 = gen_integer(min_value=1, max_value=10000)
        while value_2 == value:
            value_2 = gen_integer(min_value=1, max_value=10000)
        increment_by_2 = gen_integer(min_value=1, max_value=10000)
        while increment_by_2 == increment_by:
            increment_by_2 = gen_integer(min_value=1, max_value=10000)
        counter_value_shared = MainCounter.shared_counter(
            value=value_2, increment_by=increment_by_2
        )
        assert counter_value_shared == counter_value

        assert os.path.exists(expected_shared_file_path)

    def test_shared_sub_main_counter_class_file_path(self, scope):
        """Test file path when function is in a sub class"""
        expected_shared_file_path = os.path.join(
            get_temp_dir(),
            TEMP_ROOT_DIR,
            TEMP_FUNC_SHARED_DIR,
            '.'.join(
                [
                    scope,
                    _NAMESPACE_SCOPE_KEY_TYPE,
                    _this_module_name,
                    'MainCounter.SubCounter.shared_counter',
                ]
            ),
        )
        assert not os.path.exists(expected_shared_file_path)
        value = gen_integer(min_value=1, max_value=10000)
        increment_by = gen_integer(min_value=1, max_value=10000)
        counter_value = MainCounter.SubCounter.shared_counter(
            value=value, increment_by=increment_by
        )
        assert counter_value == value + increment_by

        value_2 = gen_integer(min_value=1, max_value=10000)
        while value_2 == value:
            value_2 = gen_integer(min_value=1, max_value=10000)
        increment_by_2 = gen_integer(min_value=1, max_value=10000)
        while increment_by_2 == increment_by:
            increment_by_2 = gen_integer(min_value=1, max_value=10000)
        counter_value_shared = MainCounter.SubCounter.shared_counter(
            value=value_2, increment_by=increment_by_2
        )
        assert counter_value_shared == counter_value

        assert os.path.exists(expected_shared_file_path)

    def test_simple_shared_counter(self):
        """The counter should never change when calling second time"""
        index_value = gen_integer(min_value=1, max_value=10000)
        index_increment_by = gen_integer(min_value=1, max_value=100)
        index_expected_value = index_value + index_increment_by
        result = simple_shared_counter_increment(index=index_value, increment_by=index_increment_by)
        assert isinstance(result, dict)
        assert 'index' in result
        assert result['index'] == index_expected_value

        index_value_2 = gen_integer(min_value=1, max_value=10000)
        while index_value_2 == index_value:
            index_value_2 = gen_integer(min_value=1, max_value=10000)
        index_increment_by_2 = gen_integer(min_value=1, max_value=100)
        while index_increment_by_2 == index_increment_by:
            index_increment_by_2 = gen_integer(min_value=1, max_value=100)
        # call the counter function a second time
        result = simple_shared_counter_increment(
            index=index_value_2, increment_by=index_increment_by_2
        )
        assert isinstance(result, dict)
        assert 'index' in result
        assert result['index'] == index_expected_value

    def test_simple_shared_counter_multiprocess(self, pool):
        """The counter should never change when calling second time, even in
        multiprocess calls"""
        pool_size = DEFAULT_POOL_SIZE
        args = [gen_integer(min_value=1, max_value=10000) for _ in range(pool_size)]
        results = pool.map(simple_shared_counter_increment_process, args)

        assert len(results) == pool_size
        # assert all the results are the same
        result = results[0]
        assert isinstance(result, dict)
        assert 'index' in result
        expected_value = result['index']
        for result in results:
            assert isinstance(result, dict)
            assert 'index' in result
            result_value = result['index']
            assert expected_value == result_value

    def test_simple_shared_counter_timeout(self):
        """The shared function should loose it's results after timeout"""
        counter_value = gen_integer(min_value=1, max_value=10000)
        result = simple_shared_counter_increment_timeout(counter_value)
        assert isinstance(result, dict)
        assert 'index' in result
        result_value = result['index']
        assert result_value == counter_value + 1

        second_counter_value = gen_integer(min_value=1, max_value=10000)
        while counter_value == second_counter_value:
            second_counter_value = gen_integer(min_value=1, max_value=10000)
        result = simple_shared_counter_increment_timeout(second_counter_value)
        assert isinstance(result, dict)
        assert 'index' in result
        second_result_value = result['index']
        # assert the value has not changed, as the shared function return
        # always the same result of the first call
        assert second_result_value != second_counter_value + 1
        assert second_result_value == result_value

        # sleep to reach timeout
        time.sleep(SIMPLE_TIMEOUT_VALUE + 1)

        timeout_counter_value = gen_integer(min_value=1, max_value=10000)
        while timeout_counter_value == counter_value:
            timeout_counter_value = gen_integer(min_value=1, max_value=10000)
        timeout_result = simple_shared_counter_increment_timeout(timeout_counter_value)
        assert isinstance(timeout_result, dict)
        assert 'index' in timeout_result
        timeout_result_value = timeout_result['index']
        assert timeout_result_value == timeout_counter_value + 1
        assert timeout_result_value != result_value

    def test_simple_shared_counter_multiprocess_timeout(self, pool):
        """The shared function should loose it's results after timeout, even
        in multiprocess calls"""
        pool_size = DEFAULT_POOL_SIZE
        counter_values = [gen_integer(min_value=1, max_value=10000) for _ in range(pool_size)]
        expected_values = [val + 1 for val in counter_values]
        results = pool.map(simple_shared_counter_increment_process_timeout, counter_values)
        assert len(results) == pool_size
        # all the results values should be equal and in expected values
        # we do not know which function got the first results
        results_values = {result.get('index') for result in results}
        assert len(results_values) == 1
        first_result_value = results_values.pop()
        assert first_result_value, expected_values

        # sleep to reach timeout
        time.sleep(SIMPLE_TIMEOUT_VALUE + 1)
        # now after the expire time the counter value should change
        second_counter_values = [
            gen_integer(min_value=1, max_value=10000) for _ in range(pool_size)
        ]
        for i in range(pool_size):
            while second_counter_values[i] in counter_values:
                second_counter_values[i] = gen_integer(min_value=1, max_value=10000)
        expected_values = [val + 1 for val in second_counter_values]
        results = pool.map(simple_shared_counter_increment_process_timeout, second_counter_values)
        assert len(results) == pool_size
        # all the results values should be equal and in expected values
        # we do not know which function got the first
        results_values = {result.get('index') for result in results}
        assert len(results_values) == 1
        second_result_value = results_values.pop()
        assert second_result_value in expected_values
        assert first_result_value != second_result_value

    def test_simple_shared_injected(self):
        """Test shared with inject and with injected_kw"""
        counter_value = gen_integer(min_value=2, max_value=10000)
        result = simple_shared_counter_with_inject(index=counter_value)
        assert isinstance(result, dict)
        result_value = result.get('index', 0)
        assert result_value == counter_value + 1

        result = simple_shared_counter_with_inject(index=counter_value)
        assert isinstance(result, dict)
        injected_result_value = result.get('index', 0)
        # when inject the shared function will modify that result by adding 100
        assert injected_result_value == result_value + 100

    def test_simple_shared_injected_multiprocess(self, pool):
        """Test shared with inject with injected_kw in multiprocess calls"""
        pool_size = DEFAULT_POOL_SIZE
        counter_values = [gen_integer(min_value=2, max_value=10000) for _ in range(pool_size)]

        # inject function must use kwargs to be injected
        results = []

        def _put_result(result):
            results.append(result)

        def _call_counter_function_processes():
            for value in counter_values:
                pool.apply_async(
                    simple_shared_counter_with_inject_multiprocess,
                    kwds=dict(index=value),
                    callback=_put_result,
                )
            pool.close()
            pool.join()

        _call_counter_function_processes()
        # I should receive a set of 2 result values
        # one value that is + 1 of the counter value of the first call of
        # one of the processes,
        # and an others with +100 from the result of the same call
        results_values_set = {result.get('index', 0) for result in results}
        assert len(results_values_set) == 2
        max_value = max(results_values_set)
        min_value = min(results_values_set)
        # asset that min_value is a result value of one of the processes
        assert min_value - 1 in counter_values
        assert max_value == min_value + 100

    def test_without_inject_kw(self):
        """Test shared with inject without injected_kw"""
        result = simple_shared_with_inject_kw_none()
        assert isinstance(result, dict)
        index_value = result.get('index')
        expected_index_value = 100
        assert index_value == expected_index_value
        result = simple_shared_with_inject_kw_none()
        assert isinstance(result, dict)
        shared_index_value = result.get('index')
        assert shared_index_value == expected_index_value + 1000

    def test_simple_shared_with_exception_restored(self, pool):
        """Test when exception raise, the exception is restored"""
        pool_size = DEFAULT_POOL_SIZE
        counter_value = gen_integer(min_value=2, max_value=10000)
        with pytest.raises(ZeroDivisionError):
            # the first process raise the original exception
            simple_shared_counter_with_exception(counter_value)

        with pytest.raises(ZeroDivisionError):
            simple_shared_counter_with_exception(counter_value)

        counter_values = [gen_integer(min_value=2, max_value=10000) for _ in range(pool_size)]

        with pytest.raises(ZeroDivisionError):
            pool.map(simple_shared_counter_with_exception, counter_values)

    def test_simple_shared_with_exception_not_restored(self, pool):
        """Test when exception raise that cannot be restored, a
        shared exception is raised"""
        pool_size = DEFAULT_POOL_SIZE
        counter_value = gen_integer(min_value=2, max_value=10000)
        with pytest.raises(NotRestorableException):
            # the first process raise the original exception
            simple_shared_counter_with_exception_not_restored(counter_value)

        with pytest.raises(SharedFunctionException):
            simple_shared_counter_with_exception_not_restored(counter_value)

        counter_values = [gen_integer(min_value=2, max_value=10000) for _ in range(pool_size)]

        with pytest.raises(SharedFunctionException):
            pool.map(simple_shared_counter_with_exception_not_restored, counter_values)

    def test_function_kw_scope(self):
        """Test that function kw is using the correct scope from argument.

        Note: shared decorator should create a new additional scope key based
            on the md5 hexdigest of the kw passed to function and that was
            declared in function_kw argument, in this concrete test this is
            related to the prefix and suffix kwargs, for each prefix, suffix
            values a new key storage is created.
        """
        prefixes = [f'pre_{i}' for i in range(10)]
        suffixes = [f'suf_{i}' for i in range(10)]
        for prefix, suffix in zip(prefixes, suffixes):
            counter_value = gen_integer(min_value=2, max_value=10000)
            inc_string = basic_shared_counter_string(
                prefix=prefix, suffix=suffix, counter=counter_value
            )
            assert inc_string.startswith(prefix)
            assert inc_string.endswith(suffix)
            # call the shared function a second time with an other value
            counter_value_2 = gen_integer(min_value=2, max_value=10000)
            while counter_value_2 == counter_value:
                counter_value_2 = gen_integer(min_value=2, max_value=10000)
            # note inverted order of kwargs
            inc_string_2 = basic_shared_counter_string(
                suffix=suffix, prefix=prefix, counter=counter_value
            )
            assert inc_string == inc_string_2
