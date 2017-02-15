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


LOGGER = logging.getLogger(__name__)


def log_debug(message):
    LOGGER.debug(message)


def get_decorated_bugs():  # pragma: no cover
    """Using Robozilla parser, get all IDs from skip_if_bug_open decorator
    and return the dictionary containing fetched data.

    Important information is stored on `bug_data` key::
        bugs[BUG_ID]['bug_data']['resolution|status|flags|whiteboard']
    """
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


def get_wontfix_bugs(bugs=None, log=None):
    """returns the ID of bugs CLOSED as WONTFIX"""
    if log is None:
        log = log_debug
    bugs = bugs or get_decorated_bugs()
    wontfixes = []
    for bug_id, data in bugs.items():
        bug_data = data.get('bug_data')
        # when not authenticated, private bugs will have no bug data
        if bug_data:
            if bug_data['resolution'] in ('WONTFIX', 'CANTFIX'):
                wontfixes.append(bug_id)
        else:
            log('bug data for bug id "{}" was not retrieved,'
                ' please review bugzilla credentials'.format(bug_id))
    return wontfixes


def group_by_key(data):
    """Gets a lsit of tuples and groups by item[0] - the key"""
    res = defaultdict(list)
    for k, v in data:
        res[k].append(v)
    return dict(res)
