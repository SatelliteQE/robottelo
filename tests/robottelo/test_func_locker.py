import multiprocessing
import os
import tempfile
import time
from pathlib import Path

import pytest

from robottelo.decorators import func_locker

_this_module_name_string = 'tests.robottelo.test_func_locker'

NAMESPACE_SCOPE = 'func_locker_unittest_scope'
NAMESPACE_SCOPE_TEST = 'func_locker_unittest_scope_test'
SCOPE = 'some_function_scope'

NAMESPACE_SCOPE_TEST_2 = 'func_locker_unittest_scope_test_2'
SCOPE_2 = 'some_function_scope_2'

# use the same number as the default jenkins process number
POOL_SIZE = 8

# patch the default scope namespace
func_locker.set_default_scope(NAMESPACE_SCOPE)


class TmpCountFile:
    def __init__(self):
        tmp_root_path = Path(func_locker.get_temp_dir()).joinpath(func_locker.TEMP_ROOT_DIR)
        tmp_root_path.mkdir(parents=True, exist_ok=True)
        self.file = tempfile.NamedTemporaryFile(delete=False, suffix='.counter', dir=tmp_root_path)
        self.file_name = self.file.name
        self.file.write(b'0')
        self.file.close()

    def read(self):
        with open(self.file_name) as cf:
            content = cf.read()

        return content

    def write(self, content):
        with open(self.file_name, 'wb') as cf:
            cf.write(content.encode('utf-8'))


counter_file = TmpCountFile()  # singleton so functions outside the test class don't need it passed


def _get_function_name_string(name, class_name=None):
    names = [_this_module_name_string]
    if class_name:
        names.append(class_name)
    names.append(name)
    return '.'.join(names)


def _get_function_lock_path(name, scope_context=None, class_name=None):
    ls = [
        func_locker.get_temp_dir(),
        func_locker.TEMP_ROOT_DIR,
        func_locker.TEMP_FUNC_LOCK_DIR,
        NAMESPACE_SCOPE,
    ]
    if scope_context:
        ls.append(scope_context)
    func_name_string = _get_function_name_string(name, class_name)
    ls.append(f'{func_name_string}.{func_locker.LOCK_FILE_NAME_EXT}')
    return os.path.join(*ls)


@func_locker.lock_function
def simple_locked_function(index=None):
    """Read the lock file and return it"""
    global counter_file
    time.sleep(0.05)
    with open(_get_function_lock_path('simple_locked_function')) as rf:
        content = rf.read()

    if index is not None:
        saved_counter = int(counter_file.read())
        counter_file.write(str(index + saved_counter))

    time.sleep(0.05)
    return os.getpid(), content


@func_locker.lock_function
def simple_recursive_lock_function():
    """Try to trigger the same lock from the same process, an exception should
    be expected
    """
    simple_recursive_lock_function()
    return 'I should not be reached'


def simple_recursive_locking_function():
    """try to trigger the same lock from the same process, an exception
    should be expected
    """
    with func_locker.locking_function(simple_locked_function):
        with func_locker.locking_function(simple_locked_function):
            pass
    return 'I should not be reached'


@func_locker.lock_function
def simple_recursive_combined_function():
    """Try to trigger the same lock from the same process, an exception should
    be expected
    """
    with func_locker.locking_function(simple_recursive_combined_function):
        pass
    return 'I should not be reached'


@func_locker.lock_function
def simple_function_to_lock():
    """Read the lock file and return it"""

    with open(_get_function_lock_path('simple_locked_function')) as rf:
        content = rf.read()
    return os.getpid(), content


def simple_with_locking_function(index=None):
    global counter_file
    time.sleep(0.05)
    with func_locker.locking_function(simple_locked_function):
        with open(_get_function_lock_path('simple_locked_function')) as rf:
            content = rf.read()

    if index is not None:
        saved_counter = int(counter_file.read())
        counter_file.write(str(index + saved_counter))

    time.sleep(0.05)
    return os.getpid(), content


class SimpleClass:
    class SubClass:
        @classmethod
        @func_locker.lock_function
        def simple_function_to_lock_cls(cls, file_path=None):
            """Return process id and file content"""
            with open(file_path) as rf:
                content = rf.read()
            return os.getpid(), content

    @classmethod
    @func_locker.lock_function
    def simple_function_to_lock_cls(cls, file_path=None):
        """Return process id and file content"""
        with open(file_path) as rf:
            content = rf.read()
        return os.getpid(), content

    @func_locker.lock_function
    def simple_function_to_lock(self, file_path=None):
        """Return process id and file content"""
        with open(file_path) as rf:
            content = rf.read()
        return os.getpid(), content


@func_locker.lock_function(scope=NAMESPACE_SCOPE_TEST, scope_context=SCOPE)
def simple_scoped_lock_function():
    """This function do nothing, when called the lock function must create
    a lock file
    """
    return None


@func_locker.lock_function
def simple_scoped_locking_function():
    """This function do nothing, when called the locking function must create
    a lock file
    """
    with func_locker.locking_function(
        simple_scoped_locking_function, scope=NAMESPACE_SCOPE_TEST_2, scope_context=SCOPE_2
    ):
        pass

    return None


def simple_function_not_locked():
    """This function do nothing, when called with locking, exception must be
    raised that this function is not locked
    """
    return None


class TestFuncLocker:
    @pytest.fixture(scope="function", autouse=True)
    def count_and_pool(self):
        global counter_file
        counter_file.write('0')
        pool = multiprocessing.Pool(POOL_SIZE)
        yield pool

        pool.terminate()
        pool.join()

    def test_simple(self):
        pid, content = simple_locked_function()
        assert str(pid) == content
        assert pid == os.getpid()

    def test_simple_with(self):
        with func_locker.locking_function(simple_function_to_lock):
            with open(_get_function_lock_path('simple_function_to_lock')) as rf:
                content = rf.read()

            assert str(os.getpid()) == content

    def test_simple_with_lock_function(self):
        """lock a function that is already decorated by lock_function"""
        with func_locker.locking_function(simple_locked_function):
            with open(_get_function_lock_path('simple_locked_function')) as rf:
                content = rf.read()

            assert str(os.getpid()) == content

    def test_locker_file_location_when_in_class(self):
        """Check the lock file location when lock function in class"""

        file_path = _get_function_lock_path('simple_function_to_lock', class_name='SimpleClass')
        if os.path.exists(file_path):
            with open(file_path) as rf:
                content = rf.read()
        else:
            content = ''
        assert str(os.getpid()) != content

        with func_locker.locking_function(SimpleClass.simple_function_to_lock):
            with open(file_path) as rf:
                content = rf.read()

        assert str(os.getpid()) == content

        file_path = _get_function_lock_path(
            'simple_function_to_lock_cls', class_name='SimpleClass'
        )
        if os.path.exists(file_path):
            with open(file_path) as rf:
                content = rf.read()
        else:
            content = ''
        assert str(os.getpid()) != content

        with func_locker.locking_function(SimpleClass.simple_function_to_lock_cls):
            with open(file_path) as rf:
                content = rf.read()

        assert str(os.getpid()) == content

        file_path = _get_function_lock_path(
            'simple_function_to_lock_cls', class_name='SimpleClass'
        )
        if os.path.exists(file_path):
            with open(file_path) as rf:
                content = rf.read()
        else:
            content = ''
        assert str(os.getpid()) != content
        _, content = SimpleClass.simple_function_to_lock_cls(file_path=file_path)
        assert str(os.getpid()) == content

        simple = SimpleClass()
        file_path = _get_function_lock_path('simple_function_to_lock', class_name='SimpleClass')
        if os.path.exists(file_path):
            with open(file_path) as rf:
                content = rf.read()
        else:
            content = ''
        assert str(os.getpid()) != content
        _, content = simple.simple_function_to_lock(file_path=file_path)
        assert os.getpid() == int(content)
        # subCalss
        file_path = _get_function_lock_path(
            'simple_function_to_lock_cls', class_name='SimpleClass.SubClass'
        )
        if os.path.exists(file_path):
            with open(file_path) as rf:
                content = rf.read()
        else:
            content = ''
        assert str(os.getpid()) != content
        _, content = SimpleClass.SubClass.simple_function_to_lock_cls(file_path=file_path)

        assert str(os.getpid()) == content

        if os.path.exists(file_path):
            with open(file_path) as rf:
                content = rf.read()
        else:
            content = ''
        assert str(os.getpid()) != content
        with func_locker.locking_function(SimpleClass.SubClass.simple_function_to_lock_cls):
            with open(file_path) as rf:
                content = rf.read()

        assert str(os.getpid()) == content

    def test_lock_in_multiprocess(self, count_and_pool):
        """Ensure that locked functions in diffrent processes are
        executed serially and wait each other.

        The strategy of this test is to have each process read the index in
        the counter file add to it it's own index and save the sum to counter
        file again:

        if the index of the process is index the saved one:
        saved_index = saved_index + index

        at the end,  the sum of all indexes must equal the content of the file
        """
        pool_size = POOL_SIZE
        pool = count_and_pool
        indexes = [index + 1 for index in range(pool_size)]
        results = pool.map(simple_locked_function, indexes)
        assert len(results) == pool_size
        pids_set = {result[0] for result in results}
        content_set = {int(result[1]) for result in results}
        # assert that all pids correspond to all saved contents
        assert pids_set == content_set
        # assert that each process was running with corresponding file content
        for pid, content in results:
            assert pid == int(content)
        # assert that the sum in counter file is the sum of indexes
        global counter_file
        assert int(counter_file.read()) == sum(indexes)

    def test_with_locking_in_multiprocess(self, count_and_pool):
        """Ensure that with locking functions in diffrent processes are
        executed serially and wait each other.

        The strategy of this test is to have each process read the index in
        the counter file add to it it's own index and save the sum to counter
        file again:

        if the index of the process is index the saved one:
        saved_index = saved_index + index

        at the end,  the sum of all indexes must equal the content of the file
        """
        pool_size = POOL_SIZE
        pool = count_and_pool
        indexes = [index + 1 for index in range(pool_size)]
        results = pool.map(simple_with_locking_function, indexes)
        assert len(results) == pool_size
        pids_set = {result[0] for result in results}
        content_set = {int(result[1]) for result in results}
        # assert that all pids correspond to all saved contents
        assert pids_set == content_set
        # assert that each process was running with corresponding file content
        for pid, content in results:
            assert pid == int(content)
        # assert that the sum in counter file is the sum of indexes
        global counter_file
        assert int(counter_file.read()) == sum(indexes)

    recursive_functions = [
        simple_recursive_lock_function,
        simple_recursive_locking_function,
        simple_recursive_combined_function,
    ]

    @pytest.mark.parametrize(
        'recursive_function', recursive_functions, ids=[f.__name__ for f in recursive_functions]
    )
    def test_recursive_lock_function(self, count_and_pool, recursive_function):
        """Ensure that recursive calls to locked function is detected using
        lock_function decorator"""
        res = count_and_pool.apply_async(recursive_function, ())
        with pytest.raises(func_locker.FunctionLockerError, match=r'.*recursion detected.*'):
            try:
                res.get(timeout=5)
            except multiprocessing.TimeoutError:
                pytest.fail('function lock recursion not detected')

    def test_scoped_lock_function(self):
        """Ensure that the lock file was created at the right location"""
        # call the function
        simple_scoped_lock_function()
        lock_file_path = os.path.join(
            func_locker.get_temp_dir(),
            func_locker.TEMP_ROOT_DIR,
            func_locker.TEMP_FUNC_LOCK_DIR,
            NAMESPACE_SCOPE_TEST,
            SCOPE,
            f'{_this_module_name_string}.simple_scoped_lock_function.lock',
        )
        assert os.path.exists(lock_file_path)

    def test_scoped_with_locking(self):
        """Ensure that the lock file was created at the right location"""
        simple_scoped_locking_function()
        lock_file_path = os.path.join(
            func_locker.get_temp_dir(),
            func_locker.TEMP_ROOT_DIR,
            func_locker.TEMP_FUNC_LOCK_DIR,
            NAMESPACE_SCOPE_TEST_2,
            SCOPE_2,
            f'{_this_module_name_string}.simple_scoped_locking_function.lock',
        )
        assert os.path.exists(lock_file_path)

    def test_negative_with_locking_not_locked(self):

        with pytest.raises(func_locker.FunctionLockerError, match=r'.*Cannot ensure locking.*'):
            with func_locker.locking_function(simple_function_not_locked):
                pass
