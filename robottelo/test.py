# -*- encoding: utf-8 -*-
"""Test utilities for writing foreman tests

All test cases for foreman tests are defined in this module and have utilities
to help writing API, CLI and UI tests.

"""
import logging
import re
import unittest2

try:
    import sauceclient
except ImportError:
    # Optional requirement, if installed robottelo will report results back to
    # saucelabs.
    sauceclient = None

from fauxfactory import gen_string
from nailgun import entities
from robottelo import manifests
from robottelo.config import settings
from robottelo.constants import (
    INTERFACE_API,
    INTERFACE_CLI,
    DEFAULT_ORG,
    DEFAULT_ORG_ID,
)

LOGGER = logging.getLogger(__name__)


class NotRaisesValueHandler(object):
    """Base class for handling exception values for AssertNotRaises. Child
    classes can be used to validate whether specific for interface expected
    value is present in exception.
    """

    def validate(self, exception):
        """Validate whether expected value is present in exception."""
        raise NotImplemented()

    @property
    def value_name(self):
        """Property used to return expected value name (e.g. 'status code' or
        'return code').
        """
        raise NotImplemented()


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


class _AssertNotRaisesContext(object):
    """A context manager used to implement :meth:`TestCase.assertNotRaises`.
    """

    def __init__(self, expected, value_handler_class, failure_exception,
                 expected_regex=None, expected_value=None, value_handler=None):
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
                raise self.failure_exception(
                    "{0} raised".format(exc_name))
            regex = self.expected_regex
            response_code = None
            if self.value_handler:
                response_code = self.value_handler.validate(exc_value)
            if regex:
                regex = True if regex.search(str(exc_value)) else False

            if response_code and regex:
                raise self.failure_exception(
                    "{0} raised with {1} {2} and {3} found in {4}"
                    .format(
                        exc_name,
                        self.value_handler.value_name,
                        self.value_handler.expected_value,
                        self.expected_regex.pattern,
                        str(exc_value),
                    )
                )
            elif response_code and regex is None:
                raise self.failure_exception(
                    "{0} raised with {1} {2}".format(
                        exc_name,
                        self.value_handler.value_name,
                        self.value_handler.expected_value,
                    )
                )
            elif regex and response_code is None:
                raise self.failure_exception(
                    "{0} raised and {1} found in {2}".format(
                        exc_name,
                        self.expected_regex.pattern,
                        str(exc_value),
                    )
                )
            else:
                # pass through
                return False

        else:
            # pass through
            return False


class AssertCliNotRaisesContextManager(_AssertNotRaisesContext):
    def __init__(self, expected, expected_regex=None, expected_value=None,
                 value_handler=None):
        super(AssertCliNotRaisesContextManager, self).__init__(
            expected, CLINotRaisesValueHandler, AssertionError, expected_regex,
            expected_value, value_handler
        )


class AssertApiNotRaisesContextManager(_AssertNotRaisesContext):
    def __init__(self, expected, expected_regex=None, expected_value=None,
                 value_handler=None):
        super(AssertApiNotRaisesContextManager, self).__init__(
            expected, APINotRaisesValueHandler, AssertionError, expected_regex,
            expected_value, value_handler
        )


class TestCase(unittest2.TestCase):
    """Robottelo test case"""

    _default_interface = INTERFACE_API
    _default_notraises_value_handler = None

    @classmethod
    def setUpClass(cls):  # noqa
        super(TestCase, cls).setUpClass()
        if not settings.configured:
            settings.configure()
        cls.logger = logging.getLogger('robottelo')
        cls.logger.info('Started setUpClass: {0}/{1}'.format(
            cls.__module__, cls.__name__))
        # NOTE: longMessage defaults to True in Python 3.1 and above
        cls.longMessage = True
        cls.foreman_user = settings.server.admin_username
        cls.foreman_password = settings.server.admin_password

    @classmethod
    def tearDownClass(cls):
        cls.logger.info('Started tearDownClass: {0}/{1}'.format(
            cls.__module__, cls.__name__))

    @classmethod
    def upload_manifest(cls, org_id, manifest, interface=None):
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
        return manifests.upload_manifest_locked(
            org_id, manifest, interface=interface)

    def assertNotRaises(self, expected_exception, callableObj=None,
                        expected_value=None, value_handler=None, *args,
                        **kwargs):
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

    def assertNotRaisesRegex(self, expected_exception, expected_regex,
                             callableObj=None, expected_value=None,
                             value_handler=None, *args, **kwargs):
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


class CLITestCase(TestCase):
    """Test case for CLI tests."""
    _default_interface = INTERFACE_CLI
    _default_notraises_value_handler = CLINotRaisesValueHandler
    _multiprocess_can_split_ = True

    def assert_error_msg(self, raise_ctx, *contents):
        """Checking error msg present on Raise Context Exception
        Raise assertion error if any of contents are not present on error msg

        :param raise_ctx: Raise Context
        :param contents: contents which must be present on message
        """
        exception = raise_ctx.exception
        error_msg = getattr(exception, 'stderr', exception.message)
        for content in contents:
            self.assertIn(content, error_msg)


class UITestCase(TestCase):
    """Test case for UI tests."""
    _default_interface = INTERFACE_API

    @classmethod
    def setUpClass(cls):  # noqa
        """Make sure that we only read configuration values once."""
        super(UITestCase, cls).setUpClass()
        cls.set_session_org()
        cls.set_session_user()
        if cls.session_user is not None:
            cls.foreman_user = cls.session_user.login
        cls.driver_name = settings.webdriver
        cls.driver_binary = settings.webdriver_binary
        cls.locale = settings.locale
        cls.server_name = settings.server.hostname
        cls.logger.info(
            u'Session set with:\n'
            u'\tUser: {cls.session_user.id}:{cls.session_user.login}\n'
            u'\tOrganization: {cls.session_org.id}:{cls.session_org.name}\n'
            u'\tWeb Driver: {cls.driver_name}\n'
            u'\tBinary: {cls.driver_binary}\n'
            u'\tLocale: {cls.locale}\n'
            u'\tServer Name: {cls.server_name}'
            .format(cls=cls)
        )

    @classmethod
    def set_session_org(cls):
        """TestCases can overwrite this method to create a different
        organization object for the session.
        """
        cls.session_org = entities.Organization(
            id=DEFAULT_ORG_ID, name=DEFAULT_ORG
        )

    @classmethod
    def set_session_user(cls):
        """Creates a new user for each session this method can be overwritten
        in TestCases in order to get different default user
        """
        try:
            username = gen_string('alpha')
            cls.session_user = entities.User(
                firstname='Robottelo User {0}'.format(username),
                login=username,
                password=cls.foreman_password,
                admin=True,
                default_organization=cls.session_org
            ).create()
        except Exception as e:
            cls.session_user = None
            cls.logger.warn('Unable to create session_user: %s', str(e))

    @classmethod
    def tearDownClass(cls):
        super(UITestCase, cls).tearDownClass()
        cls.delete_session_user()

    @classmethod
    def delete_session_user(cls):
        """Delete created session user can be overwritten in TestCase to
        bypass user deletion
        """
        if cls.session_user is not None:
            try:
                cls.session_user.delete(synchronous=False)
            except Exception as e:
                cls.logger.warn('Unable to delete session_user: %s', str(e))
            else:
                cls.logger.info(
                    'Session user is being deleted: %s', cls.session_user)

    def _saucelabs_test_result(self, session_id):
        """SauceLabs has no way to determine whether test passed or failed
        automatically, so we explicitly 'tell' it
        """
        if settings.browser == 'saucelabs' and sauceclient:
            sc = sauceclient.SauceClient(
                settings.saucelabs_user, settings.saucelabs_key)
            passed = True
            status = 'passed'
            if (len(self._outcome.errors) > 0 and
                    self in self._outcome.errors[-1]):
                passed = False
                status = 'failed'
            if (len(self._outcome.skipped) > 0 and
                    self in self._outcome.skipped[-1]):
                passed = None
                status = 'complete'
            LOGGER.debug(
                'Updating SauceLabs job "%s": name "%s" and status "%s"',
                session_id,
                str(self),
                status
            )
            sc.jobs.update_job(session_id, name=str(self), passed=passed)
