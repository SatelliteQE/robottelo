# -*- encoding: utf-8 -*-
from fauxfactory import gen_string, gen_email
from robottelo.constants import CHECKSUM_TYPE, REPO_TYPE
from robottelo.helpers import update_dictionary
from robottelo.ui.activationkey import ActivationKey
from robottelo.ui.architecture import Architecture
from robottelo.ui.computeprofile import ComputeProfile
from robottelo.ui.computeresource import ComputeResource
from robottelo.ui.configgroups import ConfigGroups
from robottelo.ui.container import Container
from robottelo.ui.contentviews import ContentViews
from robottelo.ui.discoveryrules import DiscoveryRules
from robottelo.ui.domain import Domain
from robottelo.ui.environment import Environment
from robottelo.ui.gpgkey import GPGKey
from robottelo.ui.hardwaremodel import HardwareModel
from robottelo.ui.hostcollection import HostCollection
from robottelo.ui.hostgroup import Hostgroup
from robottelo.ui.hosts import Hosts
from robottelo.ui.job_template import JobTemplate
from robottelo.ui.ldapauthsource import LdapAuthSource
from robottelo.ui.lifecycleenvironment import LifecycleEnvironment
from robottelo.ui.location import Location
from robottelo.ui.locators import menu_locators
from robottelo.ui.medium import Medium
from robottelo.ui.operatingsys import OperatingSys
from robottelo.ui.org import Org
from robottelo.ui.oscapcontent import OpenScapContent
from robottelo.ui.oscappolicy import OpenScapPolicy
from robottelo.ui.oscap_tailoringfile import OpenScapTailoringfile
from robottelo.ui.partitiontable import PartitionTable
from robottelo.ui.products import Products
from robottelo.ui.puppetclasses import PuppetClasses
from robottelo.ui.registry import Registry
from robottelo.ui.repository import Repos
from robottelo.ui.role import Role
from robottelo.ui.settings import Settings
from robottelo.ui.smart_variable import SmartVariable
from robottelo.ui.subnet import Subnet
from robottelo.ui.syncplan import Syncplan
from robottelo.ui.template import Template
from robottelo.ui.trend import Trend
from robottelo.ui.user import User
from robottelo.ui.usergroup import UserGroup
from selenium.webdriver.common.action_chains import ActionChains


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
    update_dictionary(create_args, kwargs)
    if org or loc:
        set_context(session, org=org, loc=loc, force_context=force_context)
    page()


def check_context(session):
    """Checks whether the org and loc context is set.

    :param session: The browser session.
    :return: Returns a value to set context after checking whether the
        org and loc context is set.
    :rtype: dict

    """
    current_text = session.nav.wait_until_element(
        menu_locators['menu.current_text'])
    ActionChains(session.browser).move_to_element(current_text).perform()
    current_org_text = session.nav.wait_until_element(
        menu_locators['menu.fetch_org']).text
    current_loc_text = session.nav.wait_until_element(
        menu_locators['menu.fetch_loc']).text
    return {
        'org': current_org_text == 'Any Organization',
        'loc': current_loc_text == 'Any Location',
    }


def set_context(session, org=None, loc=None, force_context=False):
    """Configures the context.

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
    select_context = check_context(session)
    # Change context only if required or when force_context is set to True
    if select_context['org'] or select_context['loc'] or force_context:
        if org:
            session.nav.go_to_select_org(org)
        if loc:
            session.nav.go_to_select_loc(loc)


def make_org(session, **kwargs):
    """Creates an organization"""

    create_args = {
        u'org_name': None,
        u'label': None,
        u'desc': None,
        u'users': None,
        u'capsules': None,
        u'subnets': None,
        u'resources': None,
        u'medias': None,
        u'templates': None,
        u'ptables': None,
        u'domains': None,
        u'envs': None,
        u'hostgroups': None,
        u'locations': None,
        u'select': True,
    }
    page = session.nav.go_to_org
    core_factory(create_args, kwargs, session, page)
    Org(session.browser).create(**create_args)


def make_loc(session, **kwargs):
    """Creates a location"""

    create_args = {
        u'name': None,
        u'parent': None,
        u'users': None,
        u'capsules': None,
        u'subnets': None,
        u'resources': None,
        u'medias': None,
        u'templates': None,
        u'ptables': None,
        u'domains': None,
        u'envs': None,
        u'hostgroups': None,
        u'organizations': None,
        u'select': True,
    }
    page = session.nav.go_to_loc
    core_factory(create_args, kwargs, session, page)
    Location(session.browser).create(**create_args)


def make_lifecycle_environment(session, org=None, loc=None,
                               force_context=True, **kwargs):
    """Creates Life-cycle Environment"""

    create_args = {
        u'name': None,
        u'description': None,
        u'prior': None,
    }
    page = session.nav.go_to_life_cycle_environments
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    LifecycleEnvironment(session.browser).create(**create_args)


def make_activationkey(session, org=None, loc=None,
                       force_context=True, **kwargs):
    """Creates Activation Key"""

    create_args = {
        u'name': None,
        u'env': None,
        u'limit': None,
        u'description': None,
        u'content_view': None,
    }
    page = session.nav.go_to_activation_keys
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    ActivationKey(session.browser).create(**create_args)


def make_product(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a product"""

    create_args = {
        u'name': None,
        u'description': None,
        u'sync_plan': None,
        u'startdate': None,
        u'create_sync_plan': False,
        u'gpg_key': None,
        u'sync_interval': None,
    }
    page = session.nav.go_to_products
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Products(session.browser).create(**create_args)


def make_repository(session, org=None, loc=None,
                    force_context=True, **kwargs):
    """Creates a repository"""

    create_args = {
        u'name': None,
        u'gpg_key': None,
        u'http': False,
        u'url': None,
        u'repo_type': REPO_TYPE['yum'],
        u'repo_checksum': CHECKSUM_TYPE['default'],
        u'upstream_repo_name': None,
        u'download_policy': None,
    }
    page = Repos(session.browser).navigate_to_entity
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Repos(session.browser).create(**create_args)


def make_contentview(
        session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a content-view"""
    create_args = {
        u'name': gen_string('alpha'),
        u'label': None,
        u'description': None,
        u'is_composite': False,
    }
    page = session.nav.go_to_content_views
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    ContentViews(session.browser).create(**create_args)


def make_gpgkey(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a gpgkey"""

    create_args = {
        u'name': None,
        u'upload_key': False,
        u'key_path': None,
        u'key_content': None,
    }
    page = session.nav.go_to_gpg_keys
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    GPGKey(session.browser).create(**create_args)


def make_subnet(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a subnet"""

    create_args = {
        u'orgs': None,
        u'subnet_name': None,
        u'subnet_network': None,
        u'subnet_mask': None,
        u'subnet_gateway': None,
        u'subnet_primarydns': None,
        u'subnet_secondarydns': None,
        u'org_select': False,
        u'domains': None
    }
    page = session.nav.go_to_subnets
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Subnet(session.browser).create(**create_args)


def make_domain(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a domain"""

    create_args = {
        u'name': None,
        u'description': None,
        u'dns_proxy': None,
    }
    page = session.nav.go_to_domains
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Domain(session.browser).create(**create_args)


def make_user(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a user"""

    password = gen_string('alpha', 6)

    create_args = {
        u'admin': False,
        u'username': None,
        u'email': gen_email(),
        u'description': None,
        u'timezone': None,
        u'password1': password,
        u'password2': password,
        u'authorized_by': u'INTERNAL',
        u'locale': None,
        u'first_name': gen_string('alpha'),
        u'last_name': gen_string('alpha'),
        u'roles': None,
        u'locations': None,
        u'organizations': None,
        u'edit': False,
        u'select': True,
        u'default_org': None,
        u'default_loc': None,
        u'submit': True,
    }
    page = session.nav.go_to_users
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    User(session.browser).create(**create_args)


def make_usergroup(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a usergroup

    :param session: For browser session.
    :param str org: To set Organization context.
    :param str loc: To set Location context.
    :param bool force_context: If ``force_context`` is ``True``, set the
        ``org`` and ``loc`` context again. This method is useful when, for
        example, creating entities with the same name but in different
        organizations.
    :param kwargs: Arbitrary keyword arguments to update create_args.
    """
    create_args = {
        u'name': None,
        u'users': None,
        u'roles': None,
        u'ext_usergrp': None,
        u'ext_authsourceid': None,
    }
    page = session.nav.go_to_user_groups
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    UserGroup(session.browser).create(**create_args)


def make_hostgroup(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a host_group"""
    create_args = {
        u'name': None,
        u'parameters_list': None,
    }
    page = session.nav.go_to_host_groups
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Hostgroup(session.browser).create(**create_args)


def make_host(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a host"""
    create_args = {
        u'name': None,
        u'puppet_classes': None,
        u'interface_parameters': None,
        u'host_parameters': None,
        u'parameters_list': None,
    }
    page = session.nav.go_to_hosts
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Hosts(session.browser).create(**create_args)


def make_discoveryrule(session, org=None, loc=None, force_context=True,
                       **kwargs):
    """Creates a discovery rule"""
    create_args = {
        u'name': None,
        u'search_rule': 'cpu_count = 1',
        u'hostgroup': None,
        u'hostname': None,
        u'host_limit': None,
        u'priority': None,
        u'enabled': True,
        u'locations': None,
        u'organizations': None,
    }
    page = session.nav.go_to_discovery_rules
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    DiscoveryRules(session.browser).create(**create_args)


def make_env(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates an Environment"""

    create_args = {
        u'name': None,
        u'orgs': None,
        u'org_select': False,
    }
    page = session.nav.go_to_environments
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Environment(session.browser).create(**create_args)


def make_resource(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a compute resource"""
    create_args = {
        u'locations': None,
        u'loc_select': False,
        u'name': None,
        u'orgs': None,
        u'org_select': False,
        u'provider_type': None,
        u'parameter_list': None,
    }
    page = session.nav.go_to_compute_resources
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    ComputeResource(session.browser).create(**create_args)


def make_media(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates an installation media"""

    create_args = {
        u'name': None,
        u'path': None,
        u'os_family': None,
    }
    page = session.nav.go_to_installation_media
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Medium(session.browser).create(**create_args)


def make_templates(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a provisioning template"""
    create_args = {
        u'name': None,
        u'template_path': None,
        u'custom_really': None,
        u'template_type': None,
        u'audit_comment': None,
        u'snippet': None,
        u'os_list': None,
        u'locations': None,
        u'organizations': None,
        u'hostgroup': None,
        u'environment': None,
    }
    page = session.nav.go_to_provisioning_templates
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Template(session.browser).create(**create_args)


def make_job_template(session, org=None, loc=None, force_context=True,
                      **kwargs):
    """Creates a job template"""
    create_args = {
        u'name': None,
        u'template_content': None,
        u'template_type': 'file',
        u'default': None,
        u'audit_comment': None,
        u'job_category': None,
        u'description_format': None,
        u'provider_type': None,
        u'effective_user_value': None,
        u'current_user': None,
        u'overridable': None,
        u'snippet': None,
    }
    page = session.nav.go_to_job_templates
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    JobTemplate(session.browser).create(**create_args)


def make_os(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates an Operating system"""

    create_args = {
        u'name': None,
        u'major_version': None,
        u'minor_version': None,
        u'description': None,
        u'os_family': None,
        u'archs': None,
        u'ptables': None,
        u'mediums': None,
        u'select': True,
        u'template': None
    }
    page = session.nav.go_to_operating_systems
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    OperatingSys(session.browser).create(**create_args)


def make_arch(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates new architecture from webUI"""

    create_args = {
        u'name': None,
        u'os_names': None
    }
    page = session.nav.go_to_architectures
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Architecture(session.browser).create(**create_args)


def make_partitiontable(session, org=None, loc=None, force_context=True,
                        **kwargs):
    """Creates new Partition table from webUI"""
    create_args = {
        u'audit_comment': None,
        u'default': False,
        u'name': None,
        u'os_family': None,
        u'snippet': None,
        u'template_path': None,
    }
    page = session.nav.go_to_partition_tables
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    PartitionTable(session.browser).create(**create_args)


def make_puppetclasses(session, org=None, loc=None, force_context=True,
                       **kwargs):
    """Creates new Puppet Classes from webUI"""

    create_args = {
        u'name': None,
        u'environment': None,
    }
    page = session.nav.go_to_puppet_classes
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    PuppetClasses(session.browser).create(**create_args)


def make_config_groups(session, org=None, loc=None, force_context=True,
                       **kwargs):
    """Creates new Config Groups from webUI"""

    create_args = {u'name': None}
    page = session.nav.go_to_config_groups
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    ConfigGroups(session.browser).create(**create_args)


def edit_param(session, org=None, loc=None,  force_context=True, **kwargs):
    """Updates selected parameter value under settings"""

    update_args = {
        u'tab_locator': None,
        u'param_name': None,
        u'param_value': None
    }
    page = session.nav.go_to_settings
    core_factory(update_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Settings(session.browser).update(**update_args)


def make_hw_model(session, org=None, loc=None,  force_context=True, **kwargs):
    """Creates new Hardware Models from webUI"""

    create_args = {
        u'name': None,
        u'hw_model': None,
        u'vendor_class': None,
        u'info': None
    }
    page = session.nav.go_to_hardware_models
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    HardwareModel(session.browser).create(**create_args)


def make_role(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates new role"""
    create_args = {
        u'name': gen_string('alpha'),
        u'locations': None,
        u'organizations': None,
    }
    page = session.nav.go_to_roles
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Role(session.browser).create(**create_args)


def make_syncplan(session, org=None, loc=None,  force_context=True, **kwargs):
    """Create new Sync Plan"""

    create_args = {
        u'name': None,
        u'description': None,
        u'startdate': None,
        u'sync_interval': None,
        u'start_hour': None,
        u'start_minute': None,
    }
    page = session.nav.go_to_sync_plans
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Syncplan(session.browser).create(**create_args)


def make_trend(session, **kwargs):
    """Creates a Trend"""
    create_args = {
        u'trend_type': None,
        u'trendable': None,
        u'name': None,
    }
    page = session.nav.go_to_trends
    core_factory(create_args, kwargs, session, page)
    Trend(session.browser).create(**create_args)


def make_ldapauth(session, **kwargs):
    """Creates a Ldap Auth"""
    create_args = {
        u'name': None,
        u'server': None,
        u'ldaps': False,
        u'port': None,
        u'server_type': None,
        u'login_name': None,
        u'first_name': None,
        u'surname': None,
        u'mail': None,
        u'photo': None,
        u'account_user': None,
        u'account_passwd': None,
        u'account_basedn': None,
        u'account_grpbasedn': None,
        u'ldap_filter': False,
        u'otf_register': True,
        u'locations': None,
        u'loc_select': False,
        u'orgs': None,
        u'org_select': False,
    }
    page = session.nav.go_to_ldap_auth
    core_factory(create_args, kwargs, session, page)
    LdapAuthSource(session.browser).create(**create_args)


def make_oscapcontent(session, org=None, loc=None, **kwargs):
    """Creates an OSCAP Content"""
    create_args = {
        u'name': None,
        u'content_path': None,
        u'content_org': None,
        u'content_loc': None,
    }
    page = session.nav.go_to_oscap_content
    core_factory(create_args, kwargs, session, page, org=org, loc=loc)
    OpenScapContent(session.browser).create(**create_args)


def make_oscappolicy(session, **kwargs):
    """Creates a OSCAP Policy"""
    create_args = {
        u'name': None,
        u'desc': None,
        u'content': None,
        u'profile': None,
        u'period': None,
        u'period_value': None,
        u'org': None,
        u'loc': None,
        u'host_group': None,
    }
    page = session.nav.go_to_oscap_policy
    core_factory(create_args, kwargs, session, page)
    OpenScapPolicy(session.browser).create(**create_args)


def make_oscap_tailoringfile(session, org=None, loc=None, **kwargs):
    """Creates an oscap tailoring file """
    create_args = {
        u'name': None,
        u'tailoring_path': None,
        u'tailoring_org': None,
        u'tailoring_loc': None,
    }
    page = session.nav.go_to_oscap_tailoringfile
    core_factory(create_args, kwargs, session, page, org=org, loc=loc)
    OpenScapTailoringfile(session.browser).create(**create_args)


def make_registry(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a Registry"""
    create_args = {
        u'name': None,
        u'url': None,
        u'description': None,
        u'username': None,
        u'password': None,
        u'orgs': None,
        u'org_select': False,
        u'locs': None,
        u'loc_select': False,
    }
    page = session.nav.go_to_registries
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Registry(session.browser).create(**create_args)


def make_container(session, org=None, loc=None, force_context=True, **kwargs):
    """Creates a docker container"""
    create_args = {
        u'resource_name': None,
        u'parameter_list': None,
        u'name': None,
        u'command': 'top',
    }
    page = session.nav.go_to_new_container
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    Container(session.browser).create(**create_args)


def make_compute_profile(session, **kwargs):
    """Creates new Compute Profile"""
    create_args = {u'name': gen_string('alpha')}
    page = session.nav.go_to_compute_profiles
    core_factory(create_args, kwargs, session, page)
    ComputeProfile(session.browser).create(**create_args)


def make_host_collection(
        session, org=None, loc=None, force_context=True, **kwargs):
    """Creates Host Collection"""
    create_args = {
        u'name': None,
        u'limit': None,
        u'description': None,
    }
    page = session.nav.go_to_host_collections
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    HostCollection(session.browser).create(**create_args)


def make_smart_variable(
        session, org=None, loc=None, force_context=True, **kwargs):
    """Creates Smart Variable"""
    create_args = {
        u'name': gen_string('alpha'),
        u'puppet_class': None,
        u'description': None,
        u'key_type': None,
        u'default_value': None,
        u'hidden_value': False,
        u'validator_type': None,
        u'validator_rule': None,
        u'matcher': None,
        u'matcher_priority': None,
        u'matcher_merge_overrides': None,
        u'matcher_merge_default': None,
        u'matcher_merge_avoid': None,
    }
    page = session.nav.go_to_puppet_classes
    core_factory(create_args, kwargs, session, page,
                 org=org, loc=loc, force_context=force_context)
    PuppetClasses(session.browser).click(
        PuppetClasses(session.browser).search(kwargs['puppet_class']))
    SmartVariable(session.browser).create(**create_args)
