# -*- encoding: utf-8 -*-

from robottelo.common.helpers import update_dictionary
from robottelo.ui.org import Org
from robottelo.ui.location import Location
from robottelo.ui.locators import menu_locators
from robottelo.ui.products import Products
from robottelo.ui.gpgkey import GPGKey


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


def make_product(session, org, loc, force_context=False, **kwargs):
    create_args = {
        'name': None,
        'description': None,
        'sync_plan': None,
        'startdate': None,
        'create_sync_plan': False,
        'gpg_key': None,
        'sync_interval': None,
    }
    create_args = update_dictionary(create_args, kwargs)
    create_args.update(kwargs)

    current_text = session.nav.wait_until_element(
        menu_locators['menu.current_text']).text
    # Change context only if required or when force_context is set to True
    if '@' not in str(current_text) or force_context:
        session.nav.go_to_select_org(org)
        session.nav.go_to_select_loc(loc)
    session.nav.go_to_products()
    Products(session.browser).create(**create_args)


def make_gpgkey(session, org, loc, force_context=False, **kwargs):
    create_args = {
        'name': None,
        'upload_key': False,
        'key_path': None,
        'key_content': None,
    }
    create_args = update_dictionary(create_args, kwargs)
    create_args.update(kwargs)

    current_text = session.nav.wait_until_element(
        menu_locators['menu.current_text']).text
    # Change context only if required or when force_context is set to True
    if '@' not in str(current_text) or force_context:
        session.nav.go_to_select_org(org)
        session.nav.go_to_select_loc(loc)
    session.nav.go_to_gpg_keys()
    GPGKey(session.browser).create(**create_args)
