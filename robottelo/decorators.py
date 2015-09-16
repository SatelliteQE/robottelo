# -*- encoding: utf-8 -*-
"""Implements various decorators"""

import bugzilla
import logging
import random
import requests
import unittest2

from ddt import data as ddt_data
from functools import wraps
from robottelo.config import conf
from robottelo.constants import BZ_OPEN_STATUSES, NOT_IMPLEMENTED
from xml.parsers.expat import ExpatError, errors
from xmlrpclib import Fault

BUGZILLA_URL = "https://bugzilla.redhat.com/xmlrpc.cgi"
LOGGER = logging.getLogger(__name__)
OBJECT_CACHE = {}
REDMINE_URL = 'http://projects.theforeman.org'

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


def data(*values):
    """
    Overrides ddt.data decorator to return only one value when doing smoke
    tests
    """
    def wrapper(func):
        """Perform smoke test attribute check"""
        smoke = conf.properties.get('main.smoke', '0') == '1'
        if smoke:
            return ddt_data(random.choice(values))(func)
        else:
            return ddt_data(*values)(func)
    return wrapper


def stubbed(reason=None):
    """Skips test due to non-implentation or some other reason."""

    # Assume 'not implemented' if no reason is given
    if reason is None:
        reason = NOT_IMPLEMENTED
    return unittest2.skip(reason)


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

    Note: The server mode is identified by ``main.project`` in
    ``robottelo.properties``

    Usage:

    To skip an entire test class::

        from robottelo.decorators import run_only_on

        @run_only_on('sat')
        Class HostTests():
            def test_create_hosts():
                # test code continues here

            def test_delete_hosts():
                # test code continues here

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

    # Validate project value
    project = project.lower()
    if project not in allowed_project_modes:
        raise ProjectModeError(
            '"{0}" is not a project mode. The allowed project modes are: {1}'
            .format(project, allowed_project_modes)
        )

    # If robottelo.properties not present or does not specify a project use sat
    robottelo_mode = conf.properties.get('main.project', 'sat').lower()

    if robottelo_mode not in allowed_project_modes:
        raise ProjectModeError(
            '"{0}" is not an acceptable "main.project" value in '
            'robottelo.properties file. The allowed project modes are: {1}'
            .format(robottelo_mode, allowed_project_modes)
        )

    # Preconditions PASS.  Now skip the test if modes does not match
    return unittest2.skipIf(
        project != robottelo_mode,
        'Server runs in "{0}" mode and this test will run '
        'only on "{1}" mode.'.format(robottelo_mode, project))


def skipRemote(func):  # noqa
    """Decorator to skip tests based on whether server is remote,
    Remote in the sense whether it is Sauce Labs"""

    remote = int(conf.properties['main.remote'])
    return unittest2.skipIf(
        remote == 1,
        "Skipping as setup related to sauce labs is missing")(func)


class BugFetchError(Exception):
    """Indicates an error occurred while fetching information about a bug."""


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
        try:
            bz_conn = bugzilla.RHBugzilla()
            bz_conn.connect(BUGZILLA_URL)
        except (TypeError, ValueError):
            raise BugFetchError(
                'Could not connect to {0}'.format(BUGZILLA_URL)
            )
        # Fetch the bug and place it in the cache.
        try:
            _bugzilla[bug_id] = bz_conn.getbugsimple(bug_id)
        except Fault as err:
            raise BugFetchError(
                'Could not fetch bug. Error: {0}'.format(err.faultString)
            )
        except ExpatError as err:
            raise BugFetchError(
                'Could not interpret bug. Error: {0}'.format(errors[err.code])
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


def bz_bug_is_open(bug_id):
    """Tell whether Bugzilla bug ``bug_id`` is open.

    If information about bug ``bug_id`` cannot be fetched, the bug is assumed
    to be closed.

    :param bug_id: The ID of the bug being inspected.
    :return: ``True`` if the bug is open. ``False`` otherwise.
    :rtype: bool

    """
    upstream_mode = conf.properties.get('main.upstream', '1') == '1'
    bug = None
    try:
        bug = _get_bugzilla_bug(bug_id)
    except BugFetchError as err:
        LOGGER.warning(err.message)
        return False
    if bug is None or bug.status not in BZ_OPEN_STATUSES:
        # if not upstream mode, verify whiteboard field for the presence of
        # 'verified in upstream' text
        if (not upstream_mode and bug.whiteboard and
                'verified in upstream' in bug.whiteboard.lower()):
            return True
        return False
    return True


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
        LOGGER.warning(err.message)
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
        @wraps(func)
        def wrapper_func(*args, **kwargs):
            """Run ``func`` or skip it by raising an exception.

            If information about bug ``bug_id`` can be fetched and the bug is
            open, skip test ``func``. Otherwise, run the test.

            :return: The return value of test method ``func``.
            :raises unittest2.SkipTest: If bug ``bug_id`` is open.
            :raises BugTypeError: If ``bug_type`` is not recognized.

            """
            if self.bug_type not in ('bugzilla', 'redmine'):
                raise BugTypeError(
                    '"{0}" is not a recognized bug type. Did you mean '
                    '"bugzilla" or "redmine"?'.format(self.bug_type)
                )
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
