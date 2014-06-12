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
from robottelo.common import conf
from robottelo.common.constants import NOT_IMPLEMENTED
from xml.parsers.expat import ExpatError, errors
from xmlrpclib import Fault


BUGZILLA_URL = "https://bugzilla.redhat.com/xmlrpc.cgi"
REDMINE_URL = 'http://projects.theforeman.org'
BUGZILLA_SKIP_TEST_STATUSES = ('NEW', 'ASSIGNED')


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


# A dict mapping bug IDs to python-bugzilla bug objects.
_bugzilla = {}


def get_bugzilla_bug(bug_id):
    """Fetch bug ``bug_id``.

    :param int bug_id: The ID of a bug in the Bugzilla database.
    :return: A FRIGGIN UNDOCUMENTED python-bugzilla THING.
    :raises BugFetchError: If an error occurs while fetching the bug. For
        example, a network timeout occurs or the bug does not exist.

    """
    # Is bug ``bug_id`` in the cache?
    if bug_id not in _bugzilla:
        # Make a network connection to the Bugzilla server.
        try:
            bz_conn = bugzilla.RHBugzilla()
            bz_conn.connect(BUGZILLA_URL)
        except (TypeError, ValueError):
            raise BugFetchError('Could not connect to {}'.format(BUGZILLA_URL))

        # Fetch the bug and place it in the cache.
        try:
            _bugzilla[bug_id] = bz_conn.getbugsimple(bug_id)
        except Fault as err:
            raise BugFetchError(
                'Could not fetch bug. Error: {}'.format(err.faultString)
            )
        except ExpatError as err:
            raise BugFetchError(
                'Could not interpret bug. Error: {}'.format(errors[err.code])
            )

    return _bugzilla[bug_id]


def skip_if_bz_bug_open(bug_id):
    """Skip the current test if bug ``bug_id`` is open or cannot be fetched.

    :param int bug_id: The ID of a bug in the Bugzilla database.
    :return: None
    :raises unittest.SkipTest: If bug ``bug_id`` is open.

    """
    try:
        bug = get_bugzilla_bug(bug_id)
    except BugFetchError as err:
        # Could not fetch bug report. Allow test to proceed.
        logging.warning(err.message)
        return None

    # If bug is open, skip the test.
    if bug.status in BUGZILLA_SKIP_TEST_STATUSES:
        raise unittest.SkipTest('Skipping test. Reason: {}'.format(bug))

    # Bug exists, but is not open. Allow the test to proceed.
    return None


_redmine = {
    'closed_statuses': None,
    'issues': {},
}


def _redmine_closed_issue_statuses():
    """Returns the Foreman's closed issue statuses IDs as a list"""

    if _redmine['closed_statuses'] is None:
        result = requests.get('%s/issue_statuses.json' % REDMINE_URL).json()
        _redmine['closed_statuses'] = []

        for issue_status in result['issue_statuses']:
            if issue_status.get('is_closed', False):
                _redmine['closed_statuses'].append(issue_status['id'])

    return _redmine['closed_statuses']


def redminebug(bug_id):
    """Decorator that skips the test if the redmine's bug is open"""

    if bug_id not in _redmine['issues']:
        result = requests.get('%s/issues/%s.json' % (REDMINE_URL, bug_id))

        if result.status_code != 200:
            logging.warning('Invalid Redmine issue #%s' % bug_id)
            return lambda func: func

        result = result.json()

        try:
            issue = result['issue']
            status_id = issue['status']['id']
            _redmine['issues'][bug_id] = status_id
        except KeyError, e:
            logging.warning(
                'Could not get info about Redmine issue #%s' % bug_id)
            logging.exception(e)
            return lambda func: func
    else:
        status_id = _redmine['issues'][bug_id]

    if status_id not in _redmine_closed_issue_statuses():
        return unittest.skip(
            'Test skipped due to Redmine issue #%s' % bug_id)
    else:
        return lambda func: func
