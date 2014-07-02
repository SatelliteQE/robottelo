# -*- encoding: utf-8 -*-

from robottelo.common.helpers import update_dictionary
from robottelo.ui.org import Org
from robottelo.ui.location import Location


def make_org(session, **kwargs):
    create_args = {
        'org_name': None,
        'parent_org': None,
        'label': None,
        'desc': None,
        'users': None,
        'proxies': None,
        'subnets': None,
        'resources': None,
        'medias': None,
        'templates': None,
        'domains': None,
        'envs': None,
        'hostgroups': None,
        'locations': None,
        'edit': False,
        'select': True,
    }
    create_args = update_dictionary(create_args, kwargs)
    create_args.update(kwargs)

    session.nav.go_to_org()
    Org(session.browser).create(**create_args)


def make_loc(session, **kwargs):
    create_args = {
        'name': None,
        'parent': None,
        'user_names': None,
    }
    create_args = update_dictionary(create_args, kwargs)
    create_args.update(kwargs)

    session.nav.go_to_loc()
    Location(session.browser).create(**create_args)
