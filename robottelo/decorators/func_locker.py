# -*- encoding: utf-8 -*-
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

            with locking_function(cls.setUpClass, 'publish_puppet_class'):
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
import logging
import os
import tempfile
import unittest2

from contextlib import contextmanager

from pytest_services.locks import file_lock

logger = logging.getLogger(__name__)

TEMP_ROOT_DIR = 'robottelo'
TEMP_FUNC_LOCK_DIR = 'lock_functions'
LOCK_DIR = None


def _get_temp_lock_function_dir(create=True):
    global LOCK_DIR
    if LOCK_DIR is not None:
        return LOCK_DIR
    tmp_lock_dir = os.path.join(tempfile.gettempdir(), TEMP_ROOT_DIR,
                                TEMP_FUNC_LOCK_DIR)
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


def _get_function_name(function, context=None):
    """Return a string representation of the function as
     module_path.Class_name.function_name, if context is defined return
     module_path.Class_name.function_name.context
     """
    names = [function.__module__]
    if hasattr(function, 'im_self'):

        self = function.im_self
        if isinstance(self, type):
            # this is a class method
            names.append(self.__name__)
        else:
            # this is an instance
            names.append(self.__class__.__name__)

    names.append(function.__name__)
    if context is not None:
        names.append(context)
    return '.'.join(names)


def _get_context_function_name(context, function):
    """Return a string representation of the function as
    module_path.Class_name.function_name
    """
    names = [function.__module__]
    if context and hasattr(context, function.__name__):

        if isinstance(context, type):
            context_class = context
        else:
            context_class = context.__class__

        if issubclass(context_class, unittest2.TestCase):
            names.append(context_class.__name__)

    names.append(function.__name__)
    return '.'.join(names)


def _get_function_lock_path(function, context=None):
    """Return the path of the file to lock"""
    return os.path.join(
        _get_temp_lock_function_dir(),
        _get_function_name(function, context=context)
    )


def _get_context_function_lock_path(context, function):
    """Return the path of the file to lock"""
    return os.path.join(
        _get_temp_lock_function_dir(),
        _get_context_function_name(context, function)
    )


def lock_function(func):
    """Generic function locker, lock any decorated function, any parallel
     pytest xdist worker will wait for this function to finish"""

    @functools.wraps(func)
    def function_wrapper(*args, **kwargs):
        if len(args) > 0:
            context = args[0]
        else:
            context = None

        lock_file_path = _get_context_function_lock_path(context, func)
        with file_lock(lock_file_path):
            logger.info('lock function using file path:{}'.format(
                lock_file_path))
            res = func(*args, **kwargs)

        return res

    return function_wrapper


@contextmanager
def locking_function(function, context=None):
    """Lock Lock a function in combination with a context
    :type function: callable
    :type context: str
    :param function: the function that is intended to be locked
    :param context: an added context string if applicable, of a concrete lock
    in combination with function.
    """
    lock_file_path = _get_function_lock_path(function, context=context)
    with file_lock(lock_file_path) as lock_handler:
        logger.info('locking function using file path:{}'.format(
            lock_file_path))
        yield lock_handler
