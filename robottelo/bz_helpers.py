# coding: utf-8
import logging
import os
from collections import defaultdict

from robottelo.config import settings
from robottelo.config.base import get_project_root
from robottelo.decorators import setting_is_set
from robozilla.filters import BZDecorator
from robozilla.parser import Parser

BASE_PATH = os.path.join(get_project_root(), 'tests', 'foreman')
VFLAGS = ['sat-{0}.{1}.{2}'.format(6, m, p) for m in '012345' for p in '0z']

LOGGER = logging.getLogger(__name__)


def log_debug(message):
    LOGGER.debug(message)


def get_decorated_bugs():  # pragma: no cover
    """Using Robozilla parser, get all IDs from skip_if_bug_open decorator
    and return the dictionary containing fetched data.

    Important information is stored on `bug_data` key::
        bugs[BUG_ID]['bug_data']['resolution|status|flags|whiteboard']
    """

    if not settings.configured:
        settings.configure()

    # look for settings bugzilla credentials
    # any way Parser bugzilla reader will check for exported environment names
    # BUGZILLA_USER_NAME and BUGZILLA_USER_PASSWORD if no credentials was
    # supplied
    bz_reader_options = {}
    bz_credentials = {}
    if setting_is_set('bugzilla'):
        bz_credentials = settings.bugzilla.get_credentials()

    bz_reader_options['credentials'] = bz_credentials
    parser = Parser(BASE_PATH, filters=[BZDecorator],
                    reader_options=bz_reader_options)
    bugs = parser.parse()
    return bugs


def get_deselect_bug_ids(bugs=None, log=None, lookup=None):  # pragma: no cover
    """returns the IDs of bugs to be deselected from test collection"""

    if not settings.configured:
        settings.configure()

    lookup = lookup or settings.bugzilla.wontfix_lookup
    if lookup is not True:
        return []

    if log is None:
        log = log_debug

    log('Fetching BZs to deselect...')
    bugs = bugs or get_decorated_bugs()
    resolution_list = []
    flag_list = []
    backlog_list = []
    for bug_id, data in bugs.items():
        bug_data = data.get('bug_data')
        # when not authenticated, private bugs will have no bug data
        if bug_data:
            if 'sat-backlog' in bug_data.get('flags', {}):
                backlog_list.append(bug_id)
            if bug_data['resolution'] in ('WONTFIX', 'CANTFIX', 'DEFERRED'):
                resolution_list.append(bug_id)
            if not any([flag in bug_data.get('flags', {}) for flag in VFLAGS]):
                # If the BZ is not flagged with any of `sat-x.x.x`
                flag_list.append(bug_id)
        else:
            log('bug data for bug id "{}" was not retrieved,'
                ' please review bugzilla credentials'.format(bug_id))

    if resolution_list:
        log('Deselected tests reason: BZ resolution %s' % resolution_list)

    if flag_list:
        log('Deselected tests reason: missing version flag %s' % flag_list)

    if backlog_list:
        log('Deselected tests reason: sat-backlog %s' % backlog_list)

    return set(resolution_list + flag_list + backlog_list)


def group_by_key(data):
    """Gets a list of tuples and groups by item[0] - the key"""
    res = defaultdict(list)
    for k, v in data:
        res[k].append(v)
    return dict(res)
