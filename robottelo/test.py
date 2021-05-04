"""Test utilities for writing foreman tests

All test cases for foreman tests are defined in this module and have utilities
to help writing API and CLI tests.

"""
import logging
import re

import unittest2

from robottelo import manifests
from robottelo.config import settings
from robottelo.constants import INTERFACE_API

LOGGER = logging.getLogger('robottelo')


class NotRaisesValueHandler:
    """Base class for handling exception values for AssertNotRaises. Child
    classes can be used to validate whether specific for interface expected
    value is present in exception.
    """

    def validate(self, exception):
        """Validate whether expected value is present in exception."""
        raise NotImplementedError()

    @property
    def value_name(self):
        """Property used to return expected value name (e.g. 'status code' or
        'return code').
        """
        raise NotImplementedError()


class APINotRaisesValueHandler(NotRaisesValueHandler):
    """AssertNotRaises value handler for API status code."""

    def __init__(self, expected_value):
        """Store expected status code."""
        self.expected_value = expected_value

    def validate(self, exception):
        """Validate whether expected status code is present in specific
        exception.
        """
        return self.expected_value == exception.response.status_code

    @property
    def value_name(self):
        """Returns API expected value name (status code)"""
        return 'HTTP status code'


class CLINotRaisesValueHandler(NotRaisesValueHandler):
    """AssertNotRaises value handler for CLI return code."""

    def __init__(self, expected_value):
        """Store expected return code"""
        self.expected_value = expected_value

    def validate(self, exception):
        """Validate whether expected return code is present in specific
        exception.
        """
        return self.expected_value == exception.return_code

    @property
    def value_name(self):
        """Returns CLI expected value name (return code)"""
        return 'return code'


class _AssertNotRaisesContext:
    """A context manager used to implement :meth:`TestCase.assertNotRaises`."""

    def __init__(
        self,
        expected,
        value_handler_class,
        failure_exception,
        expected_regex=None,
        expected_value=None,
        value_handler=None,
    ):
        self.expected = expected
        self.expected_regex = expected_regex
        self.value_handler = value_handler
        if value_handler is None and expected_value:
            self.value_handler = value_handler_class(expected_value)
        self.failure_exception = failure_exception

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            return True

        try:
            exc_name = self.expected.__name__
        except AttributeError:
            exc_name = str(self.expected)

        self.exception = exc_value  # store for later retrieval

        if issubclass(exc_type, self.expected):
            if not any((self.value_handler, self.expected_regex)):
                raise self.failure_exception(f"{exc_name} raised")
            regex = self.expected_regex
            response_code = None
            if self.value_handler:
                response_code = self.value_handler.validate(exc_value)
            if regex:
                regex = True if regex.search(str(exc_value)) else False

            if response_code and regex:
                raise self.failure_exception(
                    "{} raised with {} {} and {} found in {}".format(
                        exc_name,
                        self.value_handler.value_name,
                        self.value_handler.expected_value,
                        self.expected_regex.pattern,
                        str(exc_value),
                    )
                )
            elif response_code and regex is None:
                raise self.failure_exception(
                    "{} raised with {} {}".format(
                        exc_name, self.value_handler.value_name, self.value_handler.expected_value
                    )
                )
            elif regex and response_code is None:
                raise self.failure_exception(
                    "{} raised and {} found in {}".format(
                        exc_name, self.expected_regex.pattern, str(exc_value)
                    )
                )
            else:
                # pass through
                return False

        else:
            # pass through
            return False


class AssertCliNotRaisesContextManager(_AssertNotRaisesContext):
    def __init__(self, expected, expected_regex=None, expected_value=None, value_handler=None):
        super().__init__(
            expected,
            CLINotRaisesValueHandler,
            AssertionError,
            expected_regex,
            expected_value,
            value_handler,
        )


class AssertApiNotRaisesContextManager(_AssertNotRaisesContext):
    def __init__(self, expected, expected_regex=None, expected_value=None, value_handler=None):
        super().__init__(
            expected,
            APINotRaisesValueHandler,
            AssertionError,
            expected_regex,
            expected_value,
            value_handler,
        )


class TestCase(unittest2.TestCase):
    """Robottelo test case"""

    _default_interface = INTERFACE_API
    _default_notraises_value_handler = None

    @classmethod
    def setUpClass(cls):  # noqa
        super().setUpClass()
        if not settings.configured:
            settings.configure()
        cls.logger = logging.getLogger('robottelo')
        cls.logger.info(f'Started setUpClass: {cls.__module__}/{cls.__name__}')
        # NOTE: longMessage defaults to True in Python 3.1 and above
        cls.longMessage = True
        cls.foreman_user = settings.server.admin_username
        cls.foreman_password = settings.server.admin_password

    @classmethod
    def tearDownClass(cls):
        cls.logger.info(f'Started tearDownClass: {cls.__module__}/{cls.__name__}')

    @classmethod
    def upload_manifest(cls, org_id, manifest, interface=None, timeout=None):
        """Upload manifest locked using the default TestCase manifest if
        interface not specified.

        Usage::

            manifest = manifests.clone()
            self.upload_manifest(org_id, manifest)

            # or if you want to specify explicitly an interface
            manifest = manifests.clone()
            self.upload_manifest(org_id, manifest, interface=INTERFACE_CLI)

            # in one line
            result = self.upload_manifest(org_id, manifests.clone())
        """
        if interface is None:
            interface = cls._default_interface
        if timeout is None:
            # upload the manifest with default ssh client command timeout.
            timeout = settings.ssh_client.command_timeout
        return manifests.upload_manifest_locked(
            org_id, manifest, interface=interface, timeout=timeout
        )

    def assertNotRaises(
        self,
        expected_exception,
        callableObj=None,
        expected_value=None,
        value_handler=None,
        *args,
        **kwargs,
    ):
        """Fail if an exception of class expected_exception is raised by
        callableObj when invoked with specified positional and keyword
        arguments. If a different type of exception is raised, it will not be
        caught, and the test case will be deemed to have suffered an error,
        exactly as for an unexpected exception.

        If called with callableObj omitted or None, will return a context
        object used like this::

                with self.assertNotRaises(SomeException):
                    do_something()

        The context manager keeps a reference to the exception as the
        'exception' attribute. This allows you to inspect the exception after
        the assertion::

               with self.assertNotRaises(SomeException) as cm:
                   do_something()
               the_exception = cm.exception
               self.assertEqual(the_exception.error_code, 1)

        In addition, optional 'http_status_code' or 'cli_return_code' arg may
        be passed. This allows to specify exact HTTP status code or CLI return
        code, returned by ``requests.HTTPError`` or
        :class:`robottelo.cli.base.CLIReturnCodeError` accordingly, which
        should be validated. In such case only expected exception with expected
        response code will be caught.
        """
        context = _AssertNotRaisesContext(
            expected_exception,
            self._default_notraises_value_handler,
            self.failureException,
            expected_value=expected_value,
            value_handler=value_handler,
        )
        if callableObj is None:
            return context
        with context:
            callableObj(*args, **kwargs)

    def assertNotRaisesRegex(
        self,
        expected_exception,
        expected_regex,
        callableObj=None,
        expected_value=None,
        value_handler=None,
        *args,
        **kwargs,
    ):
        """Fail if an exception of class expected_exception is raised and the
        message in the exception matches a regex.
        """
        if expected_regex is not None:
            expected_regex = re.compile(expected_regex)
        context = _AssertNotRaisesContext(
            expected_exception,
            self._default_notraises_value_handler,
            self.failureException,
            expected_regex=expected_regex,
            expected_value=expected_value,
            value_handler=value_handler,
        )
        if callableObj is None:
            return context
        with context:
            callableObj(*args, **kwargs)


class APITestCase(TestCase):
    """Test case for API tests."""

    _default_interface = INTERFACE_API
    _default_notraises_value_handler = APINotRaisesValueHandler
    _multiprocess_can_split_ = True
