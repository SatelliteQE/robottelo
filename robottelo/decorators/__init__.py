"""Implements various decorators"""
import logging
from functools import wraps

import unittest2

from robottelo.config import settings

LOGGER = logging.getLogger('robottelo')
OBJECT_CACHE = {}


def setting_is_set(option):
    """Return either ``True`` or ``False`` if a Robottelo section setting is
    set or not respectively.
    """
    if not settings.configured:
        settings.configure()
    # Example: `settings.clients`
    if getattr(settings, option).validate():
        return False
    return True


def skip_if_not_set(*options):
    """Skips test if expected configuration is not set.

    Decorating a method::

        @skip_if_not_set('clients')
        def test_something(self):
            self.assertTrue(True)

    Decorating an entire class::

        class FeatureTestCase(robottelo.test.TestCase):

            @skip_if_not_set('clients')
            def setUp(self):
                pass

            def test_something(self):
                self.assertTrue(True)

    Or::

        class FeatureTestCase(robottelo.test.TestCase):

            @classmethod
            @skip_if_not_set('clients')
            def setUpClass(cls):
                pass

            def test_something(self):
                self.assertTrue(True)

    The last two approaches are required for decorating all test methods of a
    class, because the ``skip_if_not_set`` decorator is intended to run at
    runtime and not at import time. Decorating a class definition directly is
    not supported.

    Be aware that nosetests and standard Python unittest runners are not able
    to identify the ``SkipTest`` exception being raised on ``setUpClass`` and
    will report a failure. On the other hand, pytest will handle this as
    expected.

    :param options: List of valid `robottelo.properties` section names.
    :raises: ``unittest2.SkipTest``: If expected configuration section is not
        fully set in the `robottelo.properties` file. All required attributes
        must be set. For example, if the `server` section is enabled but its
        `hostname` attribute is not set, then a test that expects it will be
        skipped.
    """
    options_set = set(options)
    if not options_set.issubset(settings.all_features):
        invalid = options_set.difference(settings.all_features)
        raise ValueError(
            'Feature(s): "{}" not found. Available ones are: "{}".'.format(
                ', '.join(invalid), ', '.join(settings.all_features)
            )
        )

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            missing = []
            for option in options:
                # Example: `settings.clients`
                if not setting_is_set(option):
                    # List of all sections that are not fully configured
                    missing.append(option)
            if not missing:
                return func(*args, **kwargs)
            raise unittest2.SkipTest('Missing configuration for: {}.'.format(', '.join(missing)))

        return wrapper

    return decorator


def cacheable(func):
    """Decorator that makes an optional object cache available"""

    @wraps(func)
    def cacheable_function(options=None, cached=False):
        """
        This is the function being returned.
        Requires input function's name start with 'make_'
        """
        object_key = func.__name__.replace('make_', '')
        if cached is True and object_key in OBJECT_CACHE:
            return OBJECT_CACHE[object_key]
        new_object = func(options)
        if cached is True:
            OBJECT_CACHE[object_key] = new_object
        return new_object

    return cacheable_function


class ProjectModeError(Exception):
    """Indicates an error occurred while skipping based on Project Mode."""


# This definition is not being used currently as there are no multiple projects to run the tests
# Also, the dependent setting called 'project' has been removed from robottelo.properties
# We can modify this definition as per use in future and hence just keeping a 'logic' alive
def run_only_on(project):
    """Decorator to skip tests based on server mode.

    If the calling function -

    * uses 'sat' - test will be run for sat mode only

    * uses 'sam' - test will be run for sam mode only

    * does not use this decorator - test will be run for sat/sam modes

    Note: The server mode is identified by ``settings.project``.

    Usage:

    To skip a specific test::

        from robottelo.decorators import run_only_on

        @run_only_on('sat')
        def test_hostgroup_create():
            # test code continues here

    :param str project: Enter 'sat' for Satellite and 'sam' for SAM
    :returns: ``unittest2.skipIf``
    :raises: :meth:`ProjectModeError` if invalid `project` is given or invalid
        mode is specified in ``robottelo.properties`` file

    """
    allowed_project_modes = ('sat', 'sam')
    project = project.lower()

    def decorator(func):
        """Wrap test methods in order to skip the test if the test method
        project does not match the settings project.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper that will skip the test if the test method project does
            not match with the settings project.
            """
            # Validate project value
            if settings.project:
                settings_project = settings.project.lower()
            else:
                settings_project = 'sat'

            if project not in allowed_project_modes:
                raise ProjectModeError(
                    '"{}" is not a project mode. The allowed project modes '
                    'are: {}'.format(project, allowed_project_modes)
                )

            # If robottelo.properties not present or does not specify a project
            # use sat
            if settings_project not in allowed_project_modes:
                raise ProjectModeError(
                    '"{}" is not an acceptable "[robottelo] project" value '
                    'in robottelo.properties file. The allowed project modes '
                    'are: {}'.format(settings_project, allowed_project_modes)
                )

            # Preconditions PASS.  Now skip the test if modes does not match
            if project != settings_project:
                raise unittest2.SkipTest(
                    'Server runs in "{}" mode and this test will run '
                    'only on "{}" mode.'.format(settings_project, project)
                )
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator
