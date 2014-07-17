# -*- encoding: utf-8 -*-

from robottelo.common.helpers import update_dictionary
from robottelo.ui.computeresource import ComputeResource
from robottelo.ui.domain import Domain
from robottelo.ui.environment import Environment
from robottelo.ui.gpgkey import GPGKey
from robottelo.ui.hostgroup import Hostgroup
from robottelo.ui.org import Org
from robottelo.ui.location import Location
from robottelo.ui.locators import menu_locators
from robottelo.ui.medium import Medium
from robottelo.ui.products import Products
from robottelo.ui.subnet import Subnet
from robottelo.ui.template import Template
from robottelo.ui.user import User


def core_factory(create_args, kwargs, session, page, org=None, loc=None,
                 force_context=False):
    """ Performs various factory tasks.

    Updates the ``create_args`` dictionary, calls the ``set_context`` function
    to set ``org`` and ``loc`` context and finally navigates to the entities
    page.

    :param dict create_args: Default entities arguments.
    :param kwargs: Arbitrary keyword arguments to update create_args.
    :param session: The browser session.
    :param page: The entity function for navigation.
    :param str org: The organization context to set.
    :param str loc: The location context to set.
    :param bool force_context: If True set the context again.
    :return: None.

    """
    create_args = update_dictionary(create_args, kwargs)
    create_args.update(kwargs)
    if org or loc:
        set_context(session, org=org, loc=loc, force_context=force_context)
    page()


def set_context(session, org=None, loc=None, force_context=False):
    """Configures the context.

    If '@' is not present in ``context_text``, configure the context.
    When configuring the context, use ``org`` and ``loc``. If ``force_context``
    is ``True``, set the ``org`` and ``loc`` context again. This method is
    useful when, for example, creating entities with the same name but
    different organizations.

    :param session: The browser session.
    :param str org: The organization context to set.
    :param str loc: The location context to set.
    :param bool force_context: IF true set the context again.
    :return: None.

    """
    current_text = session.nav.wait_until_element(
        menu_locators['menu.current_text']).text
    # Change context only if required or when force_context is set to True
    if '@' not in str(current_text) or force_context:
        if org:
            session.nav.go_to_select_org(org)
        if loc:
            session.nav.go_to_select_loc(loc)


def make_org(session, force_context=False, **kwargs):
    """
    Creates an organization
    """
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
    page = session.nav.go_to_org
    core_factory(create_args, kwargs, session, page, force_context=False)
    Org(session.browser).create(**create_args)


def make_loc(session, force_context=False, **kwargs):
    """
    Creates a location
    """
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
    page = session.nav.go_to_loc
    core_factory(create_args, kwargs, session, page,
                 force_context=force_context)
    Location(session.browser).create(**create_args)


def make_product(session, org=None, loc=None, force_context=False, **kwargs):
    """
    Creates a product
    """
    create_args = {
        'name': None,
        'description': None,
        'sync_plan': None,
        'startdate': None,
        'create_sync_plan': False,
        'gpg_key': None,
        'sync_interval': None,
    }
    page = session.nav.go_to_products
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Products(session.browser).create(**create_args)


def make_gpgkey(session, org=None, loc=None, force_context=False, **kwargs):
    """
    Creates a gpgkey
    """
    create_args = {
        'name': None,
        'upload_key': False,
        'key_path': None,
        'key_content': None,
    }
    page = session.nav.go_to_gpg_keys
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    GPGKey(session.browser).create(**create_args)


def make_subnet(session, org=None, loc=None, force_context=False, **kwargs):
    """
    Creates a subnet
    """
    create_args = {
        'orgs': None,
        'subnet_name': None,
        'subnet_network': None,
        'subnet_mask': None,
        'org_select': False,
    }
    page = session.nav.go_to_subnets
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Subnet(session.browser).create(**create_args)


def make_domain(session, org=None, loc=None, force_context=False, **kwargs):
    """
    Creates a domain
    """
    create_args = {
        'name': None,
        'description': None,
        'dns_proxy': None,
    }
    page = session.nav.go_to_domains
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Domain(session.browser).create(**create_args)


def make_user(session, org=None, loc=None, force_context=False, **kwargs):
    """
    Creates a user
    """
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
    page = session.nav.go_to_users
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    User(session.browser).create(**create_args)


def make_hostgroup(session, org=None, loc=None, force_context=False, **kwargs):
    """
    Creates a host_group
    """
    create_args = {
        'name': None,
        'parent': None,
        'environment': None,
    }
    page = session.nav.go_to_host_groups
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Hostgroup(session.browser).create(**create_args)


def make_env(session, org=None, loc=None, force_context=False, **kwargs):
    """
    Creates an Environment
    """
    create_args = {
        'name': None,
        'orgs': None,
        'org_select': False,
    }
    page = session.nav.go_to_environments
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Environment(session.browser).create(**create_args)


def make_resource(session, org=None, loc=None, force_context=False, **kwargs):
    """
    Creates a compute resource
    """
    create_args = {
        'name': None,
        'orgs': None,
        'desc': None,
        'org_select': False,
        'provider_type': None,
        'url': None,
        'user': None,
        'password': None,
        'region': None,
        'libvirt_display': None,
        'libvirt_set_passwd': True,
        'tenant': None,
    }
    page = session.nav.go_to_compute_resources
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    ComputeResource(session.browser).create(**create_args)


def make_media(session, org=None, loc=None, force_context=False, **kwargs):
    """
    Creates an installation media
    """
    create_args = {
        'name': None,
        'path': None,
        'os_family': None,
    }
    page = session.nav.go_to_installation_media
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Medium(session.browser).create(**create_args)


def make_templates(session, org=None, loc=None, force_context=False, **kwargs):
    """
    Creates a provisioning template
    """
    create_args = {
        'name': None,
        'template_path': None,
        'custom_really': None,
        'template_type': None,
        'snippet': None,
        'os_list': None,
    }
    page = session.nav.go_to_provisioning_templates
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Template(session.browser).create(**create_args)
