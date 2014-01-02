# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Implements various decorators
"""

import bugzilla
import logging
import requests
import unittest

from robottelo.common import conf


bugzilla_log = logging.getLogger("bugzilla")
bugzilla_log.setLevel(logging.WARNING)

BUGZILLA_URL = "https://bugzilla.redhat.com/xmlrpc.cgi"
REDMINE_URL = 'http://projects.theforeman.org'


def runIf(project):
    """Decorator to skip tests based on server mode"""
    mode = conf.properties['main.project'].replace('/', '')

    if project == mode:
        return lambda func: func
    return unittest.skip("%s specific test." % project)


def bzbug(bz_id):
    """Decorator that skips the test if the bugzilla's bug is open"""
    try:
        mybz = bugzilla.RHBugzilla()
        mybz.connect(BUGZILLA_URL)
        mybug = mybz.getbugsimple(bz_id)
    except (TypeError, ValueError):
        logging.warning("Invalid Bugzilla ID {0}".format(bz_id))
        return lambda func: func
    else:
        if (mybug.status == 'NEW') or (mybug.status == 'ASSIGNED'):
            logging.debug(mybug)
            return unittest.skip("Test skipped due to %s" % mybug)
        else:
            return lambda func: func


def _redmine_closed_issue_statuses():
    """Returns the Foreman's closed issue statuses IDs as a list"""
    result = requests.get('%s/issue_statuses.json' % REDMINE_URL).json()
    closed_statuses_ids = []

    for issue_status in result['issue_statuses']:
        if issue_status.get('is_closed', False):
            closed_statuses_ids.append(issue_status['id'])

    return closed_statuses_ids


def redminebug(bug_id):
    """Decorator that skips the test if the redmine's bug is open"""
    result = requests.get('%s/issues/%s.json' % (REDMINE_URL, bug_id))

    if result.status_code != 200:
        logging.warning('Invalid Redmine issue #%s' % bug_id)
        return lambda func: func

    result = result.json()

    try:
        issue = result['issue']
        status_id = issue['status']['id']
    except KeyError, e:
        logging.warning('Could not get info about Redmine issue #%s' % bug_id)
        logging.exception(e)
        return lambda func: func
    else:
        closed_issue_statuses = _redmine_closed_issue_statuses()
        if status_id not in closed_issue_statuses:
            return unittest.skip('Test skipped due to Redmine issue #%s' %
                bug_id)
        else:
            return lambda func: func
