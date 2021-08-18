"""Implements test function locking, using pytest_services file locking

Usage::


    from robottelo.decorators.func_locker import (
        locking_function,
        lock_function,
     )

    # in many cases we have tests that need some test functions to run isolated
    # from other py.test workers when used in --boxed mode
    class SomeTestCase(TestCase):

        @classmethod
        @lock_function
        def setUpClass(cls):
            pass

    # in other cases we want only a portion of the test function to be isolated
    class SomeTestCase(TestCase):

        @classmethod
        def setUpClass(cls):

            with locking_function(cls.setUpClass,
                                  scope_context='publish_puppet_class'):
                # call the publish function


    # some tests can be in conflicts with other tests parts
    class SomeTestCase(TestCase):

       @lock_function
       def test_to_lock(self):
          pass

       def test_that_conflict_with_test_to_lock(self)
            with locking_function(self.test_to_lock):
                # do some operations that conflict with test_to_lock
"""
import functools
import inspect
import os
import tempfile
from contextlib import contextmanager

from pytest_services.locks import file_lock

from robottelo.config import settings
from robottelo.logging import logger

TEMP_ROOT_DIR = 'robottelo'
TEMP_FUNC_LOCK_DIR = 'lock_functions'
LOCK_DIR = None
LOCK_DEFAULT_TIMEOUT = 1800  # 30 minutes
LOCK_FILE_NAME_EXT = 'lock'
LOCK_DEFAULT_SCOPE = None

_DEFAULT_CLASS_NAME_DEPTH = 3


class FunctionLockerError(Exception):
    """the default function locker error"""


def set_default_scope(value):
    """Set the default namespace scope

    :type value: str or callable
    """
    global LOCK_DEFAULT_SCOPE
    LOCK_DEFAULT_SCOPE = value


def _get_default_scope():
    # this is the default locking scope
    from robottelo.config import settings

    return LOCK_DEFAULT_SCOPE or settings.server.hostname


def get_temp_dir():
    tmp_dir = settings.robottelo.tmp_dir
    if not tmp_dir:
        tmp_dir = tempfile.gettempdir()
    return tmp_dir


def _get_temp_lock_function_dir(create=True):
    global LOCK_DIR
    if LOCK_DIR is not None:
        return LOCK_DIR
    tmp_dir = get_temp_dir()
    tmp_lock_dir = os.path.join(tmp_dir, TEMP_ROOT_DIR, TEMP_FUNC_LOCK_DIR)
    if create and not os.path.exists(tmp_lock_dir):
        try:
            # it can happen that the workers try to create this path at the
            # same time
            os.makedirs(tmp_lock_dir)
        except OSError:
            if not os.path.exists(tmp_lock_dir):
                raise

    LOCK_DIR = tmp_lock_dir

    return LOCK_DIR


def _get_scope_path(scope, scope_kwargs=None, scope_context=None, create=True):
    """Returns the scopes path and create it if create is true"""
    if scope_kwargs is None:
        scope_kwargs = {}

    scope_path_list = [_get_temp_lock_function_dir(create=create)]
    if scope:
        if callable(scope):
            scope_dir_name = scope(**scope_kwargs)
        else:
            scope_dir_name = scope
        if scope_dir_name:
            scope_path_list.append(scope_dir_name)
    if scope_context:
        scope_path_list.append(scope_context)

    scope_path = os.path.join(*scope_path_list)

    if create and not os.path.exists(scope_path):
        try:
            # it can happen that the workers try to create this path at the
            # same time
            os.makedirs(scope_path)
        except OSError:
            if not os.path.exists(scope_path):
                raise

    return scope_path


def _get_function_name(function, class_name=None):
    """Return a string representation of the function as
    module_path.Class_name.function_name

    note: the class name is the first parent class
    """
    names = [function.__module__]
    if class_name:
        names.append(class_name)

    names.append(function.__name__)
    return '.'.join(names)


def _get_function_name_lock_path(function_name, scope=None, scope_kwargs=None, scope_context=None):
    """Return the path of the file to lock"""
    return os.path.join(
        _get_scope_path(scope, scope_kwargs=scope_kwargs, scope_context=scope_context),
        f'{function_name}.{LOCK_FILE_NAME_EXT}',
    )


def _check_deadlock(lock_file_path, process_id):
    """To prevent process deadlock, raise exception if the file content is the
    same as process_id

    note: this function is called before the lock

    :type lock_file_path: str
    :type process_id: str
    """
    if os.path.exists(lock_file_path):
        try:
            lock_file_handler = open(lock_file_path)
            lock_file_content = lock_file_handler.read()
        except OSError as exp:
            # do nothing, but anyway log the exception
            logger.exception(exp)
            lock_file_content = None

        if lock_file_content and lock_file_content == process_id:
            raise FunctionLockerError(
                'recursion detected: the function file already locked by the same process'
            )


def _write_content(handler, content):
    """write content to locked file"""
    handler.seek(0)
    handler.truncate()
    if content:
        handler.write(content)
    handler.flush()


def lock_function(
    function=None,
    scope=_get_default_scope,
    scope_context=None,
    scope_kwargs=None,
    timeout=LOCK_DEFAULT_TIMEOUT,
):
    """Generic function locker, lock any decorated function. Any parallel
     pytest xdist worker will wait for this function to finish

    :type function: callable
    :type scope: str or callable
    :type scope_kwargs: dict
    :type scope_context: str
    :type timeout: int

    :param function: the function that is intended to be locked
    :param scope: this parameter will define the namespace of locking
    :param scope_context: an added context string if applicable, of a concrete
           lock in combination with scope and function.
    :param scope_kwargs: kwargs to be passed to scope if is a callable
    :param timeout: the time in seconds to wait for acquiring the lock
    """
    class_names = []
    class_name = None
    index = 1
    while class_name != '<module>' and index <= _DEFAULT_CLASS_NAME_DEPTH:
        if class_name:
            class_names.append(class_name)
        class_name = inspect.getouterframes(inspect.currentframe())[index][3]
        index += 1

    class_names.reverse()
    class_name = '.'.join(class_names)

    def main_wrapper(func):

        setattr(func, '__class_name__', class_name)
        setattr(func, '__function_locked__', True)

        @functools.wraps(func)
        def function_wrapper(*args, **kwargs):
            function_name = _get_function_name(func, class_name=class_name)
            lock_file_path = _get_function_name_lock_path(
                function_name, scope=scope, scope_kwargs=scope_kwargs, scope_context=scope_context
            )
            process_id = str(os.getpid())
            # to prevent dead lock when recursively calling this function
            # check if the same process is trying to acquire the lock
            _check_deadlock(lock_file_path, process_id)

            with file_lock(lock_file_path, remove=False, timeout=timeout) as handler:
                logger.info(
                    'process id: {} lock function using file path: {}'.format(
                        process_id, lock_file_path
                    )
                )
                # write the process id that locked this function
                _write_content(handler, process_id)
                # call the locked function
                try:
                    res = func(*args, **kwargs)
                finally:
                    # clear the file
                    _write_content(handler, None)

            return res

        return function_wrapper

    def wait_function(func):
        return main_wrapper(func)

    if function:
        return main_wrapper(function)
    else:
        return wait_function


@contextmanager
def locking_function(
    function,
    scope=_get_default_scope,
    scope_context=None,
    scope_kwargs=None,
    timeout=LOCK_DEFAULT_TIMEOUT,
):
    """Lock a function in combination with a scope and scope_context.
    Any parallel pytest xdist worker will wait for this function to finish.

    :type function: callable
    :type scope: str or callable
    :type scope_kwargs: dict
    :type scope_context: str
    :type timeout: int

    :param function: the function that is intended to be locked
    :param scope: this parameter will define the namespace of locking
    :param scope_context: an added context string if applicable, of a concrete
           lock in combination with scope and function.
    :param scope_kwargs: kwargs to be passed to scope if is a callable
    :param timeout: the time in seconds to wait for acquiring the lock
    """
    if not getattr(function, '__function_locked__', False):
        raise FunctionLockerError('Cannot ensure locking when using a non locked function')
    class_name = getattr(function, '__class_name__', None)
    function_name = _get_function_name(function, class_name=class_name)
    lock_file_path = _get_function_name_lock_path(
        function_name, scope=scope, scope_kwargs=scope_kwargs, scope_context=scope_context
    )
    process_id = str(os.getpid())
    # to prevent dead lock when recursively calling this function
    # check if the same process is trying to acquire the lock
    _check_deadlock(lock_file_path, process_id)

    with file_lock(lock_file_path, remove=False, timeout=timeout) as handler:
        logger.info(
            'process id: {} - lock function name:{}  - using file path: {}'.format(
                process_id, function_name, lock_file_path
            )
        )
        # write the process id that locked this function
        _write_content(handler, process_id)
        # let the locked code run
        try:
            yield handler
        finally:
            # clear the file
            _write_content(handler, None)
