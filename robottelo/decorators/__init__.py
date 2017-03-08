# -*- encoding: utf-8 -*-
"""Implements various decorators"""
import logging
from functools import wraps, partial
from itertools import chain

import pytest
import re
import requests
import unittest2
from robozilla.bz import BZReader

from robottelo.config import settings
from robottelo.constants import BZ_OPEN_STATUSES, NOT_IMPLEMENTED
from robottelo.helpers import get_func_name
from robottelo.host_info import get_host_sat_version

LOGGER = logging.getLogger(__name__)
OBJECT_CACHE = {}
REDMINE_URL = 'http://projects.theforeman.org'

# Test Tier Decorators
# CRUD tests
tier1 = pytest.mark.tier1
# Association tests
tier2 = pytest.mark.tier2
# Systems integration tests
tier3 = pytest.mark.tier3
# Long running tests
tier4 = pytest.mark.tier4
# Destructive tests
destructive = pytest.mark.destructive

# Tests to be executed in 1 thread
run_in_one_thread = pytest.mark.run_in_one_thread

# A dict mapping bug IDs to python-bugzilla bug objects.
_bugzilla = {}

# A cache used by redmine-related functions.
#
# * _redmine['closed_statuses'] is used by `_redmine_closed_issue_statuses`
# * _redmine['issues'] is used by `skip_if_rm_bug_open`
#
_redmine = {
    'closed_statuses': None,
    'issues': {},
}


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
            'Feature(s): "{0}" not found. Available ones are: "{1}".'.format(
                ', '.join(invalid),
                ', '.join(settings.all_features)
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
            raise unittest2.SkipTest(
                'Missing configuration for: {0}.'.format(', '.join(missing)))

        return wrapper

    return decorator


def stubbed(reason=None):
    """Skips test due to non-implentation or some other reason."""
    # Assume 'not implemented' if no reason is given
    if reason is None:
        reason = NOT_IMPLEMENTED

    def wrapper(func):
        # Replicate the same behaviour as doing:
        #
        # @unittest2.skip(reason)
        # @pytest.mark.stubbed
        # def func(...):
        #     ...
        return unittest2.skip(reason)(pytest.mark.stubbed(func))

    return wrapper


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
                    '"{0}" is not a project mode. The allowed project modes '
                    'are: {1}'.format(project, allowed_project_modes)
                )

            # If robottelo.properties not present or does not specify a project
            # use sat
            if settings_project not in allowed_project_modes:
                raise ProjectModeError(
                    '"{0}" is not an acceptable "[robottelo] project" value '
                    'in robottelo.properties file. The allowed project modes '
                    'are: {1}'.format(settings_project, allowed_project_modes)
                )

            # Preconditions PASS.  Now skip the test if modes does not match
            if project != settings_project:
                raise unittest2.SkipTest(
                    'Server runs in "{0}" mode and this test will run '
                    'only on "{1}" mode.'.format(settings_project, project)
                )
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


class BugFetchError(Exception):
    """Indicates an error occurred while fetching information about a bug."""


class BZUnauthenticatedCall(Exception):
    """Indicates unauthenticated call was made into Bugzilla API"""

    def __init__(self, bug, *args, **kwargs):
        """Unauthenticated calls can be done but will not retrieve flag info.
        So basic bug data can still be checked and that is the reason a bug
        must be provided as parameter so one handling this exceptions can
        still have access to it

        :param bug: bug returned on API call
        :param args: args to be passed to Exception __init__ method
        :param kwargs: kwargs to be passed to Exception __init__ method
        """
        super(BZUnauthenticatedCall, self).__init__(*args, **kwargs)
        self.bug = bug


def _get_bugzilla_bug(bug_id):
    """Fetch bug ``bug_id``.

    :param int bug_id: The ID of a bug in the Bugzilla database.
    :return: A FRIGGIN UNDOCUMENTED python-bugzilla THING.
    :raises BugFetchError: If an error occurs while fetching the bug. For
        example, a network timeout occurs or the bug does not exist.

    """
    # Is bug ``bug_id`` in the cache?
    if bug_id in _bugzilla:
        LOGGER.debug('Bugzilla bug {0} found in cache.'.format(bug_id))
    else:
        LOGGER.info('Bugzilla bug {0} not in cache. Fetching.'.format(bug_id))
        # Make a network connection to the Bugzilla server.
        bz_credentials = {}
        if setting_is_set('bugzilla'):
            bz_credentials = settings.bugzilla.get_credentials()

        reader = BZReader(
            bz_credentials,
            include_fields=[
                'id', 'status', 'whiteboard', 'flags', 'resolution',
                'target_milestone'
            ],
            follow_clones=True
        )
        _bugzilla[bug_id] = reader.get_bug_data(bug_id)
        if not bz_credentials:
            raise BZUnauthenticatedCall(
                _bugzilla[bug_id],
                'Unauthenticated call made to BZ API, no flags data will '
                'be available'
            )
    return _bugzilla[bug_id]


# FIXME: It would be better to collect a list of statuses which indicate an
# issue is open. Doing so would make the implementation of `wrapper` (in
# `skip_if_rm_bug_open`) simpler.
def _redmine_closed_issue_statuses():
    """Return a list of issue status IDs which indicate an issue is closed.

    This list of issue status IDs is not hard-coded. Instead, the Redmine
    server is consulted when generating this list.

    :return: Statuses which indicate an issue is closed.
    :rtype: list

    """
    # Is the list of closed statuses cached?
    if _redmine['closed_statuses'] is None:
        result = requests.get('%s/issue_statuses.json' % REDMINE_URL).json()
        # We've got a list of *all* statuses. Let's throw only *closed*
        # statuses in the cache.
        _redmine['closed_statuses'] = []
        for issue_status in result['issue_statuses']:
            if issue_status.get('is_closed', False):
                _redmine['closed_statuses'].append(issue_status['id'])

    return _redmine['closed_statuses']


def _get_redmine_bug_status_id(bug_id):
    """Fetch bug ``bug_id``.

    :param int bug_id: The ID of a bug in the Redmine database.
    :return: The status ID of that bug.
    :raises BugFetchError: If an error occurs while fetching the bug. For
        example, a network timeout occurs or the bug does not exist.

    """
    if bug_id in _redmine['issues']:
        LOGGER.debug('Redmine bug {0} found in cache.'.format(bug_id))
    else:
        # Get info about bug.
        LOGGER.info('Redmine bug {0} not in cache. Fetching.'.format(bug_id))
        result = requests.get(
            '{0}/issues/{1}.json'.format(REDMINE_URL, bug_id)
        )
        if result.status_code != 200:
            raise BugFetchError(
                'Redmine bug {0} does not exist'.format(bug_id)
            )
        result = result.json()

        # Place bug into cache.
        try:
            _redmine['issues'][bug_id] = result['issue']['status']['id']
        except KeyError as err:
            raise BugFetchError(
                'Could not get status ID of Redmine bug {0}. Error: {1}'.
                format(bug_id, err)
            )

    return _redmine['issues'][bug_id]


def _to_float_version(regular_exp, possible_version):
    """extract version using regular_exp againt possible_version string.
    Returns None if extraction is not possible"""
    result = regular_exp.search(possible_version)
    if result:
        return float(result.group('version'))


_to_zstream_version = partial(
    _to_float_version, re.compile(r'sat-(?P<version>\d\.\d)\.z'))

_to_downstream_version = partial(
    _to_float_version, re.compile(r'sat-(?P<version>\d\.\d)\.\d'))

_to_target_milestone_version = partial(
    _to_float_version, re.compile(r'(?P<version>\d\.\d)\.\d'))


def _skip_downstream_condition(bug):
    """Analyse bugzila flags returning False if host version is greater or
    equal to min positive flag version, True otherwise.

    :param flags: list
    :return: bool
    """
    flags = bug.get('flags', {})
    positive_flags = [k for k, v in flags.items() if v == '+']
    zstream_versions = list(filter(
        lambda version: version is not None,
        map(_to_zstream_version, positive_flags)
    ))
    downstream_versions = list(filter(
        lambda version: version is not None,
        map(_to_downstream_version, positive_flags)
    ))

    if len(downstream_versions) == 0 and len(zstream_versions) == 0:
        return True
    target_milestone_version = bug['target_milestone']

    has_down_and_zstream = downstream_versions and zstream_versions
    if has_down_and_zstream and target_milestone_version is 'Unspecified':
        LOGGER.warning('Bugzilla with both downstream and zstream flags and '
                       'unspecified target_milestone: {}'.format(bug))
        return True

    flag_version = _to_target_milestone_version(target_milestone_version)

    if flag_version is None or not has_down_and_zstream:
        if downstream_versions:
            flag_version = min(downstream_versions)
        else:
            flag_version = min(zstream_versions)

    try:
        sat_version = float(get_host_sat_version())
    except ValueError:
        return False
    else:
        return sat_version < flag_version


def bz_bug_is_open(bug_id):
    """Tell whether Bugzilla bug ``bug_id`` is open.

    If information about bug ``bug_id`` cannot be fetched, the bug is assumed
    to be closed.

    :param bug_id: The ID of the bug being inspected.
    :return: ``True`` if the bug is open. ``False`` otherwise.
    :rtype: bool

    """
    try:
        bug = _get_bugzilla_bug(bug_id)
    except BZUnauthenticatedCall as err:
        LOGGER.warning(err)
        return _check_skip_conditions_for_bug_and_clones(err.bug, False)
    else:
        return _check_skip_conditions_for_bug_and_clones(bug)


def _check_skip_conditions_for_bug_and_clones(bug, consider_flags=True):
    """Check bug skip conditions for the bug and it's clones. If any of them
    returns False, test will not be skipped.
    Check flowchar: https://www.lucidchart.com/invitations/accept/
    3a595f1d-103f-49aa-99bf-ba1acb632b99

    :param bug: bug to analyse conditions
    :return: boolean indicating if it must be skipped or not

    """
    if bug is None:
        return False
    all_bugs = chain([bug], bug.get('other_clones', {}).values())
    skip_results = (
        _check_skip_condition_for_one_bug(bug_or_clone, consider_flags)
        for bug_or_clone in all_bugs
    )
    return all(skip_results)


def _check_skip_condition_for_one_bug(bug, consider_flags):
    """Check bug skip conditions. It will not take into account bug's flags
    if consider_flags parameter is False

    :param bug: bug to analyse conditions
    :return: boolean indicating if it must be skipped or not
    """
    # NEW, ASSIGNED, MODIFIED, POST
    if bug['status'] in BZ_OPEN_STATUSES:
        return True
    elif settings.upstream:
        return False

    def skip_upstream_conditions(flags):
        """do not test bugs with whiteboard 'verified in upstream' in
        downstream until they are in 'CLOSED' state
         Verify all conditions are True, stopping evaluation when
         first condition is False
        """
        yield bug['status'] != 'CLOSED'
        whiteboard = bug['whiteboard']
        yield whiteboard
        yield 'verified in upstream' in whiteboard.lower()

    return (all(skip_upstream_conditions(bug.get('flags', {}))) or
            (consider_flags and _skip_downstream_condition(bug)))


def rm_bug_is_open(bug_id):
    """Tell whether Redmine bug ``bug_id`` is open.

    If information about bug ``bug_id`` cannot be fetched, the bug is assumed
    to be closed.

    :param bug_id: The ID of the bug being inspected.
    :return: ``True`` if the bug is open. ``False`` otherwise.
    :rtype: bool

    """
    status_id = None
    try:
        status_id = _get_redmine_bug_status_id(bug_id)
    except BugFetchError as err:
        LOGGER.warning(err)
    if status_id is None or status_id in _redmine_closed_issue_statuses():
        return False
    return True


class BugTypeError(Exception):
    """Indicates that an incorrect bug type was specified."""


class skip_if_bug_open(object):  # noqa pylint:disable=C0103,R0903
    """A decorator that can be used to skip a unit test."""

    def __init__(self, bug_type, bug_id):
        """Record decorator arguments.

        :param str bug_type: Either 'bugzilla' or 'redmine'.
        :param int bug_id: The ID of the bug to check when the decorator is
            run.

        """
        self.bug_type = bug_type
        self.bug_id = bug_id

    def __call__(self, func):
        """Define and return a replacement for ``func``.

        :param func: The function being decorated.

        """
        self.register_bug_id(func)

        if self.bug_type not in ('bugzilla', 'redmine'):
            raise BugTypeError(
                '"{0}" is not a recognized bug type. Did you mean '
                '"bugzilla" or "redmine"?'.format(self.bug_type)
            )

        @wraps(func)
        def wrapper_func(*args, **kwargs):
            """Run ``func`` or skip it by raising an exception.

            If information about bug ``bug_id`` can be fetched and the bug is
            open, skip test ``func``. Otherwise, run the test.

            :return: The return value of test method ``func``.
            :raises unittest2.SkipTest: If bug ``bug_id`` is open.
            :raises BugTypeError: If ``bug_type`` is not recognized.

            """
            if self.bug_type == 'bugzilla' and bz_bug_is_open(self.bug_id):
                LOGGER.debug(
                    'Skipping test %s in module %s due to Bugzilla bug #%s',
                    func.__name__,
                    func.__module__,
                    self.bug_id
                )
                raise unittest2.SkipTest(
                    'Skipping test due to open Bugzilla bug #{0}.'
                    ''.format(self.bug_id)
                )
            if self.bug_type == 'redmine' and rm_bug_is_open(self.bug_id):
                LOGGER.debug(
                    'Skipping test %s in module %s due to Redmine bug #%s',
                    func.__name__,
                    func.__module__,
                    self.bug_id
                )
                raise unittest2.SkipTest(
                    'Skipping test due to open Redmine bug #{0}.'
                    ''.format(self.bug_id)
                )
            # Run the test method.
            return func(*args, **kwargs)

        # This function replaces what is being decorated.
        return wrapper_func

    def register_bug_id(self, func):  # pragma: no cover
        """Every time the test is decorated, takes the BZ number and
        register it in pytest global namespace variable to be accessible in
        conftest in order to perform the filtering of test collection
        """
        bz_namespace = getattr(pytest, 'bugzilla', None)
        if bz_namespace:
            bz_namespace.decorated_functions.append(
                (get_func_name(func), str(self.bug_id))
            )


class run_in_one_thread_if_bug_open(skip_if_bug_open, object):
    """A decorator that sets pytest marker and allows to select test that
    should be run sequentially only if bug is open.
    """

    _wrapper = run_in_one_thread

    def __call__(self, func):
        """Return unchanged function or function decorated with
        `pytest.mark.run_in_one_thread` marker decorator if bug is open.

        :param func: The function being decorated.

        :return: The return value of test method ``func``.
        :raises BugTypeError: If ``bug_type`` is not recognized.
        """
        self.register_bug_id(func)

        if self.bug_type not in ('bugzilla', 'redmine'):
            raise BugTypeError(
                '"{0}" is not a recognized bug type. Did you mean '
                '"bugzilla" or "redmine"?'.format(self.bug_type)
            )

        if (self.bug_type == 'bugzilla' and bz_bug_is_open(self.bug_id)) or \
                (self.bug_type == 'redmine' and rm_bug_is_open(self.bug_id)):
            func = self._wrapper(func)
        return func
