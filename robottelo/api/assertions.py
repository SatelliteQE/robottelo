# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from robottelo.test import AssertApiNotRaisesContextManager


def assert_api_not_raises(
    expected_exception, callable_obj=None, expected_value=None, value_handler=None, *args, **kwargs
):
    """Fail if an exception of class expected_exception is raised by
    callableObj when invoked with specified positional and keyword
    arguments. If a different type of exception is raised, it will not be
    caught, and the test case will be deemed to have suffered an error,
    exactly as for an unexpected exception.

    If called with callableObj omitted or None, will return a context
    object used like this::

            with assert_api_not_raises(SomeException):
                do_something()

    The context manager keeps a reference to the exception as the
    'exception' attribute. This allows you to inspect the exception after
    the assertion::

           with assert_api_not_raises(SomeException) as cm:
               do_something()
           the_exception = cm.exception
           assert the_exception.error_code == 1

    In addition, optional 'http_status_code' arg may
    be passed. This allows to specify exact HTTP status code, returned by
    ``requests.HTTPError``, which should be validated. In such case only
    expected exception with expected response code will be caught.
    """
    context = AssertApiNotRaisesContextManager(
        expected_exception, expected_value=expected_value, value_handler=value_handler
    )
    if callable_obj is None:
        return context
    with context:
        callable_obj(*args, **kwargs)


def assert_api_not_raises_regex(
    expected_exception,
    expected_regex,
    callable_obj=None,
    expected_value=None,
    value_handler=None,
    *args,
    **kwargs
):
    """Fail if an exception of class expected_exception is raised and the
    message in the exception matches a regex.
    """
    if expected_regex is not None:
        expected_regex = re.compile(expected_regex)
    context = AssertApiNotRaisesContextManager(
        expected_exception,
        expected_regex=expected_regex,
        expected_value=expected_value,
        value_handler=value_handler,
    )
    if callable_obj is None:
        return context
    with context:
        callable_obj(*args, **kwargs)
