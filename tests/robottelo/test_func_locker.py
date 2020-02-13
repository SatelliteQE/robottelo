# coding: utf-8
import multiprocessing
import os
import tempfile
import time

from unittest2 import TestCase

from robottelo.decorators.func_locker import FunctionLockerError
from robottelo.decorators.func_locker import get_temp_dir
from robottelo.decorators.func_locker import LOCK_FILE_NAME_EXT
from robottelo.decorators.func_locker import lock_function
from robottelo.decorators.func_locker import locking_function
from robottelo.decorators.func_locker import set_default_scope
from robottelo.decorators.func_locker import TEMP_FUNC_LOCK_DIR
from robottelo.decorators.func_locker import TEMP_ROOT_DIR

_this_module_name_string = 'tests.robottelo.test_func_locker'

NAMESPACE_SCOPE = 'func_locker_unittest_scope'
NAMESPACE_SCOPE_TEST = 'func_locker_unittest_scope_test'
SCOPE = 'some_function_scope'

NAMESPACE_SCOPE_TEST_2 = 'func_locker_unittest_scope_test_2'
SCOPE_2 = 'some_function_scope_2'

# use the same number as the default jenkins process number
POOL_SIZE = 8

# patch the default scope namespace
set_default_scope(NAMESPACE_SCOPE)

_counter_file_name = None


def _init_counter_file():

    global _counter_file_name

    tmp_root_path = os.path.join(get_temp_dir(), TEMP_ROOT_DIR)
    if not os.path.exists(tmp_root_path):
        os.mkdir(tmp_root_path)

    _counter_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix='.counter',
        dir=tmp_root_path
    )
    _counter_file_name = _counter_file.name
    _counter_file.write('0'.encode('utf-8'))
    _counter_file.close()


def _read_counter_file():
    global _counter_file_name
    with open(_counter_file_name, 'r') as cf:
        content = cf.read()

    return content


def _write_to_counter_file(content):
    global _counter_file_name
    with open(_counter_file_name, 'wb') as cf:
        cf.write(content.encode('utf-8'))


def _get_function_name_string(name, class_name=None):
    names = [_this_module_name_string]
    if class_name:
        names.append(class_name)
    names.append(name)
    return '.'.join(names)


def _get_function_lock_path(name, scope_context=None, class_name=None):
    ls = [get_temp_dir(), TEMP_ROOT_DIR, TEMP_FUNC_LOCK_DIR,
          NAMESPACE_SCOPE]
    if scope_context:
        ls.append(scope_context)
    ls.append('{0}.{1}'.format(_get_function_name_string(name, class_name),
                               LOCK_FILE_NAME_EXT)
              )
    return os.path.join(*ls)


@lock_function
def simple_locked_function(index=None):
    """Read the lock file and return it"""
    time.sleep(0.05)
    with open(_get_function_lock_path('simple_locked_function'), 'r') as rf:
        content = rf.read()

    if index is not None:
        saved_counter = int(_read_counter_file())
        _write_to_counter_file(str(index + saved_counter))

    time.sleep(0.05)
    return os.getpid(), content


@lock_function
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
    with locking_function(simple_locked_function):
        with locking_function(simple_locked_function):
            pass
    return 'I should not be reached'


@lock_function
def simple_recursive_combined_function():
    """Try to trigger the same lock from the same process, an exception should
    be expected
    """
    with locking_function(simple_recursive_combined_function):
        pass
    return 'I should not be reached'


@lock_function
def simple_function_to_lock():
    """Read the lock file and return it"""

    with open(_get_function_lock_path('simple_locked_function'), 'r') as rf:
        content = rf.read()
    return os.getpid(), content


def simple_with_locking_function(index=None):
    time.sleep(0.05)
    with locking_function(simple_locked_function):
        with open(_get_function_lock_path('simple_locked_function'),
                  'r') as rf:
            content = rf.read()

    if index is not None:
        saved_counter = int(_read_counter_file())
        _write_to_counter_file(str(index + saved_counter))

    time.sleep(0.05)
    return os.getpid(), content


class SimpleClass(object):

    class SubClass(object):

        @classmethod
        @lock_function
        def simple_function_to_lock_cls(cls, file_path=None):
            """Return process id and file content"""
            with open(file_path, 'r') as rf:
                content = rf.read()
            return os.getpid(), content

    @classmethod
    @lock_function
    def simple_function_to_lock_cls(cls, file_path=None):
        """Return process id and file content"""
        with open(file_path, 'r') as rf:
            content = rf.read()
        return os.getpid(), content

    @lock_function
    def simple_function_to_lock(self, file_path=None):
        """Return process id and file content"""
        with open(file_path, 'r') as rf:
            content = rf.read()
        return os.getpid(), content


@lock_function(scope=NAMESPACE_SCOPE_TEST, scope_context=SCOPE)
def simple_scoped_lock_function():
    """This function do nothing, when called the lock function must create
    a lock file
    """
    return None


@lock_function
def simple_scoped_locking_function():
    """This function do nothing, when called the locking function must create
    a lock file
    """
    with locking_function(simple_scoped_locking_function,
                          scope=NAMESPACE_SCOPE_TEST_2, scope_context=SCOPE_2):
        pass

    return None


def simple_function_not_locked():
    """This function do nothing, when called with locking, exception must be
    raised that this function is not locked
    """
    return None


class FuncLockerTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        _init_counter_file()

    def setUp(self):
        _write_to_counter_file('0')
        self.pool = multiprocessing.Pool(POOL_SIZE)

    def tearDown(self):
        self.pool.terminate()
        self.pool.join()

    def test_simple(self):
        pid, content = simple_locked_function()
        self.assertEqual(str(pid), content)
        self.assertEqual(pid, os.getpid())

    def test_simple_with(self):
        with locking_function(simple_function_to_lock):
            with open(_get_function_lock_path('simple_function_to_lock'),
                      'r') as rf:
                content = rf.read()

            self.assertEqual(str(os.getpid()), content)

    def test_simple_with_lock_function(self):
        """lock a function that is already decorated by lock_function"""
        with locking_function(simple_locked_function):
            with open(_get_function_lock_path('simple_locked_function'),
                      'r') as rf:
                content = rf.read()

            self.assertEqual(str(os.getpid()), content)

    def test_locker_file_location_when_in_class(self):
        """Check the lock file location when lock function in class"""

        file_path = _get_function_lock_path(
            'simple_function_to_lock', class_name='SimpleClass')
        if os.path.exists(file_path):
            with open(file_path, 'r') as rf:
                content = rf.read()
        else:
            content = ''
        self.assertNotEqual(str(os.getpid()), content)

        with locking_function(SimpleClass.simple_function_to_lock):
            with open(file_path, 'r') as rf:
                content = rf.read()

        self.assertEqual(str(os.getpid()), content)

        file_path = _get_function_lock_path(
            'simple_function_to_lock_cls', class_name='SimpleClass')
        if os.path.exists(file_path):
            with open(file_path, 'r') as rf:
                content = rf.read()
        else:
            content = ''
        self.assertNotEqual(str(os.getpid()), content)

        with locking_function(SimpleClass.simple_function_to_lock_cls):
            with open(file_path, 'r') as rf:
                content = rf.read()

        self.assertEqual(str(os.getpid()), content)

        file_path = _get_function_lock_path(
            'simple_function_to_lock_cls', class_name='SimpleClass')
        if os.path.exists(file_path):
            with open(file_path, 'r') as rf:
                content = rf.read()
        else:
            content = ''
        self.assertNotEqual(str(os.getpid()), content)
        _, content = SimpleClass.simple_function_to_lock_cls(
            file_path=file_path)
        self.assertEqual(str(os.getpid()), content)

        simple = SimpleClass()
        file_path = _get_function_lock_path(
            'simple_function_to_lock', class_name='SimpleClass')
        if os.path.exists(file_path):
            with open(file_path, 'r') as rf:
                content = rf.read()
        else:
            content = ''
        self.assertNotEqual(str(os.getpid()), content)
        _, content = simple.simple_function_to_lock(file_path=file_path)
        self.assertEqual(os.getpid(), int(content))
        # subCalss
        file_path = _get_function_lock_path(
            'simple_function_to_lock_cls', class_name='SimpleClass.SubClass')
        if os.path.exists(file_path):
            with open(file_path, 'r') as rf:
                content = rf.read()
        else:
            content = ''
        self.assertNotEqual(str(os.getpid()), content)
        _, content = SimpleClass.SubClass.simple_function_to_lock_cls(
            file_path=file_path)

        self.assertEqual(str(os.getpid()), content)

        if os.path.exists(file_path):
            with open(file_path, 'r') as rf:
                content = rf.read()
        else:
            content = ''
        self.assertNotEqual(str(os.getpid()), content)
        with locking_function(
                SimpleClass.SubClass.simple_function_to_lock_cls):
            with open(file_path, 'r') as rf:
                content = rf.read()

        self.assertEqual(str(os.getpid()), content)

    def test_lock_in_multiprocess(self):
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
        pool = self.pool
        indexes = [index+1 for index in range(pool_size)]
        results = pool.map(simple_locked_function, indexes)
        self.assertEqual(len(results), pool_size)
        pids_set = {result[0] for result in results}
        content_set = {int(result[1]) for result in results}
        # assert that all pids correspond to all saved contents
        self.assertEqual(pids_set, content_set)
        # assert that each process was running with corresponding file content
        for pid, content in results:
            self.assertEqual(pid, int(content))
        # assert that the sum in counter file is the sum of indexes
        self.assertEqual(int(_read_counter_file()), sum(indexes))

    def test_with_locking_in_multiprocess(self):
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
        pool = self.pool
        indexes = [index + 1 for index in range(pool_size)]
        results = pool.map(simple_with_locking_function, indexes)
        self.assertEqual(len(results), pool_size)
        pids_set = {result[0] for result in results}
        content_set = {int(result[1]) for result in results}
        # assert that all pids correspond to all saved contents
        self.assertEqual(pids_set, content_set)
        # assert that each process was running with corresponding file content
        for pid, content in results:
            self.assertEqual(pid, int(content))
        # assert that the sum in counter file is the sum of indexes
        self.assertEqual(int(_read_counter_file()), sum(indexes))

    def test_recursive_lock_function(self):
        """Ensure that recursive calls to locked function is detected using
        lock_function decorator"""
        res = self.pool.apply_async(simple_recursive_lock_function, ())
        with self.assertRaises(FunctionLockerError) as context:
            try:
                res.get(timeout=5)
            except multiprocessing.TimeoutError:
                self.fail('function lock recursion not detected')

        self.assertIn('recursion detected', str(context.exception))

    def test_recursive_locking_function(self):
        """Ensure that recursive calls to locked function is detected using
        decorator and with statement"""
        res = self.pool.apply_async(simple_recursive_locking_function, ())
        with self.assertRaises(FunctionLockerError) as context:
            try:
                res.get(timeout=5)
            except multiprocessing.TimeoutError:
                self.fail('function lock recursion not detected')

        self.assertIn('recursion detected', str(context.exception))

    def test_recursive_combined_function(self):
        """Ensure that recursive calls to locked function is detected using
        decorator and with statement"""
        res = self.pool.apply_async(simple_recursive_combined_function, ())
        with self.assertRaises(FunctionLockerError) as context:
            try:
                res.get(timeout=5)
            except multiprocessing.TimeoutError:
                self.fail('function lock recursion not detected')

        self.assertIn('recursion detected', str(context.exception))

    def test_scoped_lock_function(self):
        """Ensure that the lock file was created at the right location"""
        # call the function
        simple_scoped_lock_function()
        lock_file_path = os.path.join(
            get_temp_dir(),
            TEMP_ROOT_DIR,
            TEMP_FUNC_LOCK_DIR,
            NAMESPACE_SCOPE_TEST,
            SCOPE,
            '{}.simple_scoped_lock_function.lock'.format(
                _this_module_name_string)
        )
        self.assertTrue(os.path.exists(lock_file_path))

    def test_scoped_with_locking(self):
        """Ensure that the lock file was created at the right location"""
        simple_scoped_locking_function()
        lock_file_path = os.path.join(
            get_temp_dir(),
            TEMP_ROOT_DIR,
            TEMP_FUNC_LOCK_DIR,
            NAMESPACE_SCOPE_TEST_2,
            SCOPE_2,
            '{}.simple_scoped_locking_function.lock'.format(
                _this_module_name_string)
        )
        self.assertTrue(os.path.exists(lock_file_path))

    def test_negative_with_locking_not_locked(self):

        with self.assertRaises(FunctionLockerError) as context:
            with locking_function(simple_function_not_locked):
                pass

        self.assertIn('Cannot ensure locking', str(context.exception))
