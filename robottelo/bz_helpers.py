# coding: utf-8
import os
from collections import defaultdict
from robottelo.config.settings import get_project_root
from robozilla.filters import BZDecorator
from robozilla.parser import Parser

BASE_PATH = os.path.join(get_project_root(), 'tests', 'foreman')


def get_decorated_bugs():  # pragma: no cover
    """Using Robozilla parser, get all IDs from skip_if_bug_open decorator
    and return the dictionary containing fetched data.

    Important information is stored on `bug_data` key::
        bugs[BUG_ID]['bug_data']['resolution|status|flags|whiteboard']
    """
    parser = Parser(BASE_PATH, filters=[BZDecorator])
    bugs = parser.parse()
    return bugs


def get_wontfix_bugs(bugs=None):
    """returns the ID of bugs CLOSED as WONTFIX"""
    bugs = bugs or get_decorated_bugs()
    wontfixes = []
    for bug_id, data in bugs.items():
        if data['bug_data']['resolution'] in ('WONTFIX', 'CANTFIX'):
            wontfixes.append(bug_id)
    return wontfixes


def group_by_key(data):
    """Gets a lsit of tuples and groups by item[0] - the key"""
    res = defaultdict(list)
    for k, v in data:
        res[k].append(v)
    return dict(res)


def get_func_name(func):
    """Given a func object return standardized name to use across project"""
    return '{0}.{1}'.format(func.__module__, func.__name__)
