# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements various decorators
"""

import bugzilla
import logging
import random
import requests

import sys
if sys.hexversion >= 0x2070000:
    import unittest
else:
    import unittest2 as unittest


from ddt import data as ddt_data
from functools import wraps
from robottelo.common.constants import NOT_IMPLEMENTED
from robottelo.common import conf
from xml.parsers.expat import ExpatError, errors
from xmlrpclib import Fault


BUGZILLA_URL = "https://bugzilla.redhat.com/xmlrpc.cgi"
BUGZILLA_OPEN_BUG_STATUSES = ('NEW', 'ASSIGNED')
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

# Increase the level of third party packages logging
logging.getLogger('bugzilla').setLevel(logging.WARNING)
logging.getLogger(
    'requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)


def data(*values):
    """
    Overrides ddt.data decorator to return only one value when doing smoke
    tests
    """
    def wrapper(func):
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
    return unittest.skip(reason)


def runIf(project):
    """Decorator to skip tests based on server mode"""
    mode = conf.properties['main.project'].replace('/', '')

    if project == mode:
        return lambda func: func
    return unittest.skip("%s specific test." % project)


def skipRemote(func):
    """Decorator to skip tests based on whether server is remote,
    Remote in the sense whether it is Sauce Labs"""

    remote = int(conf.properties['main.remote'])
    return unittest.skipIf(
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
        logging.info('Bugzilla bug {0} found in cache.'.format(bug_id))
    else:
        logging.info('Bugzilla bug {0} not in cache. Fetching.'.format(bug_id))
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


def skip_if_bz_bug_open(bug_id):
    """A decorator that returns a customized decorator.

    The customized decorator will either run or skip its decorated function
    based on the status of Bugzilla bug ``bug_id``.

    ``skip_if_bz_bug_open`` should only be applied to methods in a
    ``unittest.TestCase`` subclass.

    :param str bug_id: The ID of a bug in the Bugzilla database.
    :return: A customized decorator function.
    :rtype: function

    """
    def decorator(decorated_func):
        """Make ``decorated_func`` available through ``wrapper``.

        The ``wrapper`` function exists to prevent the business logic contained
        therein from executing when this decorator is evaluated.

        :param function decorated_func: The function to be wrapped.
        :return: A function decorated with ``wrapper``.
        :rtype: function

        """
        @wraps(decorated_func)
        def wrapper(*args, **kwargs):
            """Run ``decorated_func`` or skip it by raising an exception.

            If information about bug ``bug_id`` can be fetched and the bug is
            open, skip test ``decorated_func``. Otherwise, run the test.

            :return: The return value of function ``decorated_func``.
            :raises unittest.SkipTest: If bug ``bug_id`` is open.

            """
            # Fetch info about bug `bug_id`.
            bug = None
            try:
                bug = _get_bugzilla_bug(bug_id)
            except BugFetchError as err:
                logging.warning(err.message)

            # Skip or run the test.
            if bug is not None and bug.status in BUGZILLA_OPEN_BUG_STATUSES:
                raise unittest.SkipTest(
                    'Skipping test due to open bug report: {0}'.format(bug)
                )
            return decorated_func(*args, **kwargs)

        return wrapper
    return decorator


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
        logging.info('Redmine bug {0} found in cache.'.format(bug_id))
    else:
        # Get info about bug.
        logging.info('Redmine bug {0} not in cache. Fetching.'.format(bug_id))
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


def skip_if_rm_bug_open(bug_id):
    """A decorator that returns a customized decorator.

    The customized decorator will either run or skip its decorated function
    based on the status of Redmine bug ``bug_id``.

    ``skip_if_bz_bug_open`` should only be applied to methods in a
    ``unittest.TestCase`` subclass.

    :param str bug_id: The ID of a bug in the Redmine database.
    :return: A customized decorator function.
    :rtype: function

    """
    def decorator(decorated_func):
        """Make ``decorated_func`` available through ``wrapper``.

        The ``wrapper`` function exists to prevent the business logic contained
        therein from executing when this decorator is evaluated.

        :param function decorated_func: The function to be wrapped.
        :return: A function decorated with ``wrapper``.
        :rtype: function

        """
        @wraps(decorated_func)
        def wrapper(*args, **kwargs):
            """Run ``decorated_func`` or skip it by raising an exception.

            If information about bug ``bug_id`` can be fetched and the bug is
            open, skip test ``decorated_func``. Otherwise, run the test.

            :return: The return value of function ``decorated_func``.
            :raises unittest.SkipTest: If bug ``bug_id`` is open.

            """
            # Fetch status ID of bug `bug_id`.
            status_id = None
            try:
                status_id = _get_redmine_bug_status_id(bug_id)
            except BugFetchError as err:
                logging.warning(err.message)

            # Skip or run the test.
            if status_id is not None \
                    and status_id not in _redmine_closed_issue_statuses():
                raise unittest.SkipTest(
                    'Skipping test due to open Redmine bug #{0}'.format(bug_id)
                )
            return decorated_func(*args, **kwargs)

        return wrapper
    return decorator
