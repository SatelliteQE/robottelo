# -*- encoding: utf-8 -*-

from robottelo.common.helpers import update_dictionary
from robottelo.ui.domain import Domain
from robottelo.ui.gpgkey import GPGKey
from robottelo.ui.hostgroup import Hostgroup
from robottelo.ui.org import Org
from robottelo.ui.location import Location
from robottelo.ui.locators import menu_locators
from robottelo.ui.products import Products
from robottelo.ui.subnet import Subnet
from robottelo.ui.user import User


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
        'users': None,
        'proxies': None,
        'subnets': None,
        'resources': None,
        'medias': None,
        'templates': None,
        'domains': None,
        'envs': None,
        'hostgroups': None,
        'organizations': None,
        'edit': False,
        'select': True,
    }
    create_args = update_dictionary(create_args, kwargs)
    create_args.update(kwargs)

    session.nav.go_to_loc()
    Location(session.browser).create(**create_args)


def make_product(session, org=None, loc=None, **kwargs):
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
    if '@' not in str(current_text):
        if org:
            session.nav.go_to_select_org(org)
        if loc:
            session.nav.go_to_select_loc(loc)
    session.nav.go_to_products()
    Products(session.browser).create(**create_args)


def make_gpgkey(session, org=None, loc=None, **kwargs):
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
    if '@' not in str(current_text):
        if org:
            session.nav.go_to_select_org(org)
        if loc:
            session.nav.go_to_select_loc(loc)
    session.nav.go_to_gpg_keys()
    GPGKey(session.browser).create(**create_args)


def make_subnet(session, org=None, loc=None, **kwargs):
    create_args = {
        'orgs': None,
        'subnet_name': None,
        'subnet_network': None,
        'subnet_mask': None,
        'org_select': False,
    }
    create_args = update_dictionary(create_args, kwargs)
    create_args.update(kwargs)

    current_text = session.nav.wait_until_element(
        menu_locators['menu.current_text']).text
    # Change context only if required or when force_context is set to True
    if '@' not in str(current_text):
        if org:
            session.nav.go_to_select_org(org)
        if loc:
            session.nav.go_to_select_loc(loc)
    session.nav.go_to_subnets()
    Subnet(session.browser).create(**create_args)


def make_domain(session, org=None, loc=None, **kwargs):
    create_args = {
        'name': None,
        'description': None,
        'dns_proxy': None,
    }
    create_args = update_dictionary(create_args, kwargs)
    create_args.update(kwargs)

    current_text = session.nav.wait_until_element(
        menu_locators['menu.current_text']).text
    # Change context only if required or when force_context is set to True
    if '@' not in str(current_text):
        if org:
            session.nav.go_to_select_org(org)
        if loc:
            session.nav.go_to_select_loc(loc)
    session.nav.go_to_domains()
    Domain(session.browser).create(**create_args)


def make_user(session, org=None, loc=None, **kwargs):
    create_args = {
        'username': None,
        'email': None,
        'password1': None,
        'password2': None,
        'authorized_by': "INTERNAL",
        'locale': None,
        'first_name': None,
        'last_name': None,
        'roles': None,
        'locations': None,
        'organizations': None,
        'edit': False,
        'select': True,
    }
    create_args = update_dictionary(create_args, kwargs)
    create_args.update(kwargs)

    current_text = session.nav.wait_until_element(
        menu_locators['menu.current_text']).text
    # Change context only if required or when force_context is set to True
    if '@' not in str(current_text):
        if org:
            session.nav.go_to_select_org(org)
        if loc:
            session.nav.go_to_select_loc(loc)
    session.nav.go_to_users()
    User(session.browser).create(**create_args)


def make_hostgroup(session, org=None, loc=None, **kwargs):
    create_args = {
        'name': None,
        'parent': None,
        'environment': None,
    }
    create_args = update_dictionary(create_args, kwargs)
    create_args.update(kwargs)

    current_text = session.nav.wait_until_element(
        menu_locators['menu.current_text']).text
    # Change context only if required or when force_context is set to True
    if '@' not in str(current_text):
        if org:
            session.nav.go_to_select_org(org)
        if loc:
            session.nav.go_to_select_loc(loc)
    session.nav.go_to_host_groups()
    Hostgroup(session.browser).create(**create_args)
