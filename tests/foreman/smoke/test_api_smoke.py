# -*- encoding: utf-8 -*-
"""Smoke tests for the ``API`` end-to-end scenario."""
from fauxfactory import gen_string
from nailgun import client
from robottelo.api import utils
from robottelo.api.utils import status_code_error
from robottelo.common.constants import (
    DEFAULT_LOC, DEFAULT_ORG, FAKE_0_PUPPET_REPO, GOOGLE_CHROME_REPO)
from robottelo.common.decorators import bz_bug_is_open, skip_if_bug_open
from robottelo.common.helpers import get_distro_info, get_server_credentials
from robottelo.common import conf
from robottelo.common import helpers
from robottelo.common import manifests
from robottelo import entities
from robottelo.vm import VirtualMachine
from unittest import TestCase
import httplib
import random
# (too many public methods) pylint: disable=R0904

API_PATHS = {
    # flake8:noqa (line-too-long) pylint:disable=C0301
    u'activation_keys': (
        u'/katello/api/activation_keys',
        u'/katello/api/activation_keys',
        u'/katello/api/activation_keys/:id',
        u'/katello/api/activation_keys/:id',
        u'/katello/api/activation_keys/:id',
        u'/katello/api/activation_keys/:id/add_subscriptions',
        u'/katello/api/activation_keys/:id/content_override',
        u'/katello/api/activation_keys/:id/copy',
        u'/katello/api/activation_keys/:id/host_collections/available',
        u'/katello/api/activation_keys/:id/product_content',
        u'/katello/api/activation_keys/:id/releases',
        u'/katello/api/activation_keys/:id/remove_subscriptions',
    ),
    u'api': (),
    u'architectures': (
        u'/api/architectures',
        u'/api/architectures',
        u'/api/architectures/:id',
        u'/api/architectures/:id',
        u'/api/architectures/:id',
    ),
    u'audits': (
        u'/api/audits',
        u'/api/audits/:id',
    ),
    u'auth_source_ldaps': (
        u'/api/auth_source_ldaps',
        u'/api/auth_source_ldaps',
        u'/api/auth_source_ldaps/:id',
        u'/api/auth_source_ldaps/:id',
        u'/api/auth_source_ldaps/:id',
    ),
    u'autosign': (
        u'/api/smart_proxies/smart_proxy_id/autosign',
    ),
    u'base': (),
    u'bookmarks': (
        u'/api/bookmarks',
        u'/api/bookmarks',
        u'/api/bookmarks/:id',
        u'/api/bookmarks/:id',
        u'/api/bookmarks/:id',
    ),
    u'candlepin_proxies': (
        u'/katello/api/systems/:id/enabled_repos',
    ),
    u'capsule_content': (
        u'/katello/api/capsules/:id/content/available_lifecycle_environments',
        u'/katello/api/capsules/:id/content/lifecycle_environments',
        u'/katello/api/capsules/:id/content/lifecycle_environments',
        u'/katello/api/capsules/:id/content/lifecycle_environments/:environment_id',
        u'/katello/api/capsules/:id/content/sync',
    ),
    u'capsules': (
        u'/katello/api/capsules',
        u'/katello/api/capsules/:id',
    ),
    u'common_parameters': (
        u'/api/common_parameters',
        u'/api/common_parameters',
        u'/api/common_parameters/:id',
        u'/api/common_parameters/:id',
        u'/api/common_parameters/:id',
    ),
    u'compute_attributes': (
        u'/api/compute_resources/:compute_resource_id/compute_profiles/:compute_profile_id/compute_attributes',
        u'/api/compute_resources/:compute_resource_id/compute_profiles/:compute_profile_id/compute_attributes/:id',
    ),
    u'compute_profiles': (
        u'/api/compute_profiles',
        u'/api/compute_profiles',
        u'/api/compute_profiles/:id',
        u'/api/compute_profiles/:id',
        u'/api/compute_profiles/:id',
    ),
    u'compute_resources': (
        u'/api/compute_resources',
        u'/api/compute_resources',
        u'/api/compute_resources/:id',
        u'/api/compute_resources/:id',
        u'/api/compute_resources/:id',
        u'/api/compute_resources/:id/associate',
        u'/api/compute_resources/:id/available_clusters',
        u'/api/compute_resources/:id/available_clusters/:cluster_id/available_resource_pools',
        u'/api/compute_resources/:id/available_folders',
        u'/api/compute_resources/:id/available_images',
        u'/api/compute_resources/:id/available_networks',
        u'/api/compute_resources/:id/available_storage_domains',
    ),
    u'config_groups': (
        u'/api/config_groups',
        u'/api/config_groups',
        u'/api/config_groups/:id',
        u'/api/config_groups/:id',
        u'/api/config_groups/:id',
    ),
    u'config_templates': (
        u'/api/config_templates',
        u'/api/config_templates',
        u'/api/config_templates/build_pxe_default',
        u'/api/config_templates/:id',
        u'/api/config_templates/:id',
        u'/api/config_templates/:id',
    ),
    u'content_uploads': (
        u'/katello/api/repositories/:repository_id/content_uploads',
        u'/katello/api/repositories/:repository_id/content_uploads/:id',
        u'/katello/api/repositories/:repository_id/content_uploads/:id',
    ),
    u'content_view_filter_rules': (
        u'/katello/api/content_view_filters/:content_view_filter_id/rules',
        u'/katello/api/content_view_filters/:content_view_filter_id/rules',
        u'/katello/api/content_view_filters/:content_view_filter_id/rules/:id',
        u'/katello/api/content_view_filters/:content_view_filter_id/rules/:id',
        u'/katello/api/content_view_filters/:content_view_filter_id/rules/:id',
    ),
    u'content_view_filters': (
        u'/katello/api/content_views/:content_view_id/filters',
        u'/katello/api/content_views/:content_view_id/filters',
        u'/katello/api/content_views/:content_view_id/filters/:id',
        u'/katello/api/content_views/:content_view_id/filters/:id',
        u'/katello/api/content_views/:content_view_id/filters/:id',
        u'/katello/api/content_views/:content_view_id/filters/:id/available_errata',
        u'/katello/api/content_views/:content_view_id/filters/:id/available_package_groups',
    ),
    u'content_view_puppet_modules': (
        u'/katello/api/content_views/:content_view_id/content_view_puppet_modules',
        u'/katello/api/content_views/:content_view_id/content_view_puppet_modules',
        u'/katello/api/content_views/:content_view_id/content_view_puppet_modules/:id',
        u'/katello/api/content_views/:content_view_id/content_view_puppet_modules/:id',
        u'/katello/api/content_views/:content_view_id/content_view_puppet_modules/:id',
    ),
    u'content_views': (
        u'/katello/api/content_views/:id',
        u'/katello/api/content_views/:id',
        u'/katello/api/content_views/:id',
        u'/katello/api/content_views/:id/available_puppet_module_names',
        u'/katello/api/content_views/:id/available_puppet_modules',
        u'/katello/api/content_views/:id/copy',
        u'/katello/api/content_views/:id/environments/:environment_id',
        u'/katello/api/content_views/:id/history',
        u'/katello/api/content_views/:id/publish',
        u'/katello/api/content_views/:id/remove',
        u'/katello/api/organizations/:organization_id/content_views',
        u'/katello/api/organizations/:organization_id/content_views',
    ),
    u'containers': (
        u'/docker/api/v2/containers',
        u'/docker/api/v2/containers',
        u'/docker/api/v2/containers/:id',
        u'/docker/api/v2/containers/:id',
        u'/docker/api/v2/containers/:id/logs',
        u'/docker/api/v2/containers/:id/power',
    ),
    u'content_reports':(
        u'/katello/api/content_reports/status_trend',
        u'/katello/api/content_reports/system_status',
        u'/katello/api/content_reports/system_trend',
    ),
    u'content_view_versions': (
        u'/katello/api/content_view_versions',
        u'/katello/api/content_view_versions/:id',
        u'/katello/api/content_view_versions/:id',
        u'/katello/api/content_view_versions/:id/promote',
        u'/katello/api/content_view_versions/incremental_update',
    ),
    u'dashboard': (
        u'/api/dashboard',
    ),
    u'discovered_hosts': (
        u'/api/v2/discovered_hosts',
        u'/api/v2/discovered_hosts',
        u'/api/v2/discovered_hosts/auto_provision_all',
        u'/api/v2/discovered_hosts/facts',
        u'/api/v2/discovered_hosts/:id',
        u'/api/v2/discovered_hosts/:id',
        u'/api/v2/discovered_hosts/:id',
        u'/api/v2/discovered_hosts/:id/auto_provision',
        u'/api/v2/discovered_hosts/:id/reboot',
        u'/api/v2/discovered_hosts/:id/refresh_facts',
    ),
    u'discovery_rules': (
        u'/api/v2/discovery_rules',
        u'/api/v2/discovery_rules',
        u'/api/v2/discovery_rules/:id',
        u'/api/v2/discovery_rules/:id',
        u'/api/v2/discovery_rules/:id',
    ),
    u'disks': (
        u'/bootdisk/api',
        u'/bootdisk/api/generic',
        u'/bootdisk/api/hosts/:host_id',
    ),
    u'distributions': (
        u'/katello/api/repositories/:repository_id/distributions',
        u'/katello/api/repositories/:repository_id/distributions/:id',
    ),
    u'docker_images': (
        u'/katello/api/docker_images',
        u'/katello/api/docker_images/:id',
    ),
    u'docker_tags': (
        u'/katello/api/docker_tags',
        u'/katello/api/docker_tags/:id',
    ),
    u'domains': (
        u'/api/domains',
        u'/api/domains',
        u'/api/domains/:id',
        u'/api/domains/:id',
        u'/api/domains/:id',
    ),
    u'environments': (
        u'/api/environments',
        u'/api/environments',
        u'/api/environments/:id',
        u'/api/environments/:id',
        u'/api/environments/:id',
        u'/api/smart_proxies/:id/import_puppetclasses',
    ),
    u'errata': (
        u'/katello/api/errata',
        u'/katello/api/errata/compare',
        u'/katello/api/errata/:id',
    ),
    u'external_usergroups': (
        u'/api/usergroups/:usergroup_id/external_usergroups',
        u'/api/usergroups/:usergroup_id/external_usergroups',
        u'/api/usergroups/:usergroup_id/external_usergroups/:id',
        u'/api/usergroups/:usergroup_id/external_usergroups/:id',
        u'/api/usergroups/:usergroup_id/external_usergroups/:id',
        u'/api/usergroups/:usergroup_id/external_usergroups/:id/refresh',
    ),
    u'fact_values': (
        u'/api/fact_values',
    ),
    u'filters': (
        u'/api/filters',
        u'/api/filters',
        u'/api/filters/:id',
        u'/api/filters/:id',
        u'/api/filters/:id',
    ),
    u'foreman_tasks': (
        u'/foreman_tasks/api/tasks/bulk_search',
        u'/foreman_tasks/api/tasks/:id',
    ),
    u'gpg_keys': (
        u'/katello/api/gpg_keys',
        u'/katello/api/gpg_keys',
        u'/katello/api/gpg_keys/:id',
        u'/katello/api/gpg_keys/:id',
        u'/katello/api/gpg_keys/:id',
        u'/katello/api/gpg_keys/:id/content',
    ),
    u'home': (
        u'/api',
        u'/api/status',
    ),
    u'host_classes': (
        u'/api/hosts/:host_id/puppetclass_ids',
        u'/api/hosts/:host_id/puppetclass_ids',
        u'/api/hosts/:host_id/puppetclass_ids/:id',
    ),
    u'host_collections': (
        u'/katello/api/host_collections',
        u'/katello/api/host_collections',
        u'/katello/api/host_collections/:id',
        u'/katello/api/host_collections/:id',
        u'/katello/api/host_collections/:id',
        u'/katello/api/host_collections/:id/add_systems',
        u'/katello/api/host_collections/:id/copy',
        u'/katello/api/host_collections/:id/remove_systems',
        u'/katello/api/host_collections/:id/systems',
    ),
    u'hostgroup_classes': (
        u'/api/hostgroups/:hostgroup_id/puppetclass_ids',
        u'/api/hostgroups/:hostgroup_id/puppetclass_ids',
        u'/api/hostgroups/:hostgroup_id/puppetclass_ids/:id',
    ),
    u'hostgroups': (
        u'/api/hostgroups',
        u'/api/hostgroups',
        u'/api/hostgroups/:id',
        u'/api/hostgroups/:id',
        u'/api/hostgroups/:id',
        u'/api/hostgroups/:id/clone',
    ),
    u'hosts': (
        u'/api/hosts',
        u'/api/hosts',
        u'/api/hosts/facts',
        u'/api/hosts/:id',
        u'/api/hosts/:id',
        u'/api/hosts/:id',
        u'/api/hosts/:id/boot',
        u'/api/hosts/:id/disassociate',
        u'/api/hosts/:id/power',
        u'/api/hosts/:id/puppetrun',
        u'/api/hosts/:id/status',
    ),
    u'images': (
        u'/api/compute_resources/:compute_resource_id/images',
        u'/api/compute_resources/:compute_resource_id/images',
        u'/api/compute_resources/:compute_resource_id/images/:id',
        u'/api/compute_resources/:compute_resource_id/images/:id',
        u'/api/compute_resources/:compute_resource_id/images/:id',
    ),
    u'interfaces': (
        u'/api/hosts/:host_id/interfaces',
        u'/api/hosts/:host_id/interfaces',
        u'/api/hosts/:host_id/interfaces/:id',
        u'/api/hosts/:host_id/interfaces/:id',
        u'/api/hosts/:host_id/interfaces/:id',
    ),
    u'lifecycle_environments': (
        u'/katello/api/environments',
        u'/katello/api/environments',
        u'/katello/api/environments/:id',
        u'/katello/api/environments/:id',
        u'/katello/api/environments/:id',
        u'/katello/api/organizations/:organization_id/environments/:id/repositories',
        u'/katello/api/organizations/:organization_id/environments/paths',
    ),
    u'locations': (
        u'/api/locations',
        u'/api/locations',
        u'/api/locations/:id',
        u'/api/locations/:id',
        u'/api/locations/:id',
    ),
    u'mail_notifications': (
        u'/api/mail_notifications',
        u'/api/mail_notifications/:id',
    ),
    u'media': (
        u'/api/media',
        u'/api/media',
        u'/api/media/:id',
        u'/api/media/:id',
        u'/api/media/:id',
    ),
    u'models': (
        u'/api/models',
        u'/api/models',
        u'/api/models/:id',
        u'/api/models/:id',
        u'/api/models/:id',
    ),
    u'operatingsystems': (
        u'/api/operatingsystems',
        u'/api/operatingsystems',
        u'/api/operatingsystems/:id',
        u'/api/operatingsystems/:id',
        u'/api/operatingsystems/:id',
        u'/api/operatingsystems/:id/bootfiles',
    ),
    u'organizations': (
        u'/katello/api/organizations',
        u'/katello/api/organizations',
        u'/katello/api/organizations/:id',
        u'/katello/api/organizations/:id',
        u'/katello/api/organizations/:id',
        u'/katello/api/organizations/:id/autoattach_subscriptions',
        u'/katello/api/organizations/:id/redhat_provider',
        u'/katello/api/organizations/:id/repo_discover',
        u'/katello/api/organizations/:label/cancel_repo_discover',
        u'/katello/api/organizations/:label/download_debug_certificate',
    ),
    u'os_default_templates': (
        u'/api/operatingsystems/:operatingsystem_id/os_default_templates',
        u'/api/operatingsystems/:operatingsystem_id/os_default_templates',
        u'/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
        u'/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
        u'/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
    ),
    u'override_values': (
        u'/api/smart_variables/:smart_variable_id/override_values',
        u'/api/smart_variables/:smart_variable_id/override_values',
        u'/api/smart_variables/:smart_variable_id/override_values/:id',
        u'/api/smart_variables/:smart_variable_id/override_values/:id',
        u'/api/smart_variables/:smart_variable_id/override_values/:id',
    ),
    u'package_groups': (
        u'/katello/api/package_groups',
        u'/katello/api/package_groups/:id',
    ),
    u'packages': (
        u'/katello/api/packages',
        u'/katello/api/packages/:id',
    ),
    u'parameters': (
        u'/api/hosts/:host_id/parameters',
        u'/api/hosts/:host_id/parameters',
        u'/api/hosts/:host_id/parameters',
        u'/api/hosts/:host_id/parameters/:id',
        u'/api/hosts/:host_id/parameters/:id',
        u'/api/hosts/:host_id/parameters/:id',
    ),
    u'permissions': (
        u'/api/permissions',
        u'/api/permissions/:id',
        u'/api/permissions/resource_types',
    ),
    u'ping': (
        u'/katello/api/ping',
        u'/katello/api/status',
    ),
    u'plugins': (
        u'/api/plugins',
    ),
    u'products_bulk_actions': (
        u'/katello/api/products/bulk/destroy',
        u'/katello/api/products/bulk/sync_plan',
    ),
    u'products': (
        u'/katello/api/products',
        u'/katello/api/products',
        u'/katello/api/products/:id',
        u'/katello/api/products/:id',
        u'/katello/api/products/:id',
        u'/katello/api/products/:id/sync',
    ),
    u'ptables': (
        u'/api/ptables',
        u'/api/ptables',
        u'/api/ptables/:id',
        u'/api/ptables/:id',
        u'/api/ptables/:id',
    ),
    u'puppetclasses': (
        u'/api/puppetclasses',
        u'/api/puppetclasses',
        u'/api/puppetclasses/:id',
        u'/api/puppetclasses/:id',
        u'/api/puppetclasses/:id',
    ),
    u'puppet_modules': (
        u'/katello/api/puppet_modules',
        u'/katello/api/puppet_modules/:id',
    ),
    u'realms': (
        u'/api/realms',
        u'/api/realms',
        u'/api/realms/:id',
        u'/api/realms/:id',
        u'/api/realms/:id',
    ),
    u'reports': (
        u'/api/hosts/:host_id/reports/last',
        u'/api/reports',
        u'/api/reports',
        u'/api/reports/:id',
        u'/api/reports/:id',
    ),
    u'repositories_bulk_actions': (
        u'/katello/api/repositories/bulk/destroy',
        u'/katello/api/repositories/bulk/sync',
    ),
    u'repositories': (
        u'/katello/api/repositories',
        u'/katello/api/repositories',
        u'/katello/api/repositories/:id',
        u'/katello/api/repositories/:id',
        u'/katello/api/repositories/:id',
        u'/katello/api/repositories/:id/gpg_key_content',
        u'/katello/api/repositories/:id/import_uploads',
        u'/katello/api/repositories/:id/sync',
        u'/katello/api/repositories/:id/upload_content',
    ),
    u'repository_sets': (
        u'/katello/api/products/:product_id/repository_sets',
        u'/katello/api/products/:product_id/repository_sets/:id',
        u'/katello/api/products/:product_id/repository_sets/:id/available_repositories',
        u'/katello/api/products/:product_id/repository_sets/:id/disable',
        u'/katello/api/products/:product_id/repository_sets/:id/enable',
    ),
    u'roles': (
        u'/api/roles',
        u'/api/roles',
        u'/api/roles/:id',
        u'/api/roles/:id',
        u'/api/roles/:id',
    ),
    u'root': (),
    u'settings': (
        u'/api/settings',
        u'/api/settings/:id',
        u'/api/settings/:id',
    ),
    u'smart_class_parameters': (
        u'/api/smart_class_parameters',
        u'/api/smart_class_parameters/:id',
        u'/api/smart_class_parameters/:id',
    ),
    u'smart_proxies': (
        u'/api/smart_proxies',
        u'/api/smart_proxies',
        u'/api/smart_proxies/:id',
        u'/api/smart_proxies/:id',
        u'/api/smart_proxies/:id',
        u'/api/smart_proxies/:id/import_puppetclasses',
        u'/api/smart_proxies/:id/refresh',
    ),
    u'smart_variables': (
        u'/api/smart_variables',
        u'/api/smart_variables',
        u'/api/smart_variables/:id',
        u'/api/smart_variables/:id',
        u'/api/smart_variables/:id',
    ),
    u'statistics': (
        u'/api/statistics',
    ),
    u'subnets': (
        u'/api/subnets',
        u'/api/subnets',
        u'/api/subnets/:id',
        u'/api/subnets/:id',
        u'/api/subnets/:id',
    ),
    u'subscriptions': (
        u'/katello/api/organizations/:organization_id/subscriptions',
        u'/katello/api/organizations/:organization_id/subscriptions/delete_manifest',
        u'/katello/api/organizations/:organization_id/subscriptions/:id',
        u'/katello/api/organizations/:organization_id/subscriptions/manifest_history',
        u'/katello/api/organizations/:organization_id/subscriptions/refresh_manifest',
        u'/katello/api/organizations/:organization_id/subscriptions/upload',
        u'/katello/api/subscriptions/:id',
        u'/katello/api/subscriptions/:id',
        u'/katello/api/systems/:system_id/subscriptions/available',
    ),
    u'sync_plans': (
        u'/katello/api/organizations/:organization_id/sync_plans',
        u'/katello/api/organizations/:organization_id/sync_plans/:id',
        u'/katello/api/organizations/:organization_id/sync_plans/:id',
        u'/katello/api/organizations/:organization_id/sync_plans/:id',
        u'/katello/api/organizations/:organization_id/sync_plans/:id/add_products',
        u'/katello/api/organizations/:organization_id/sync_plans/:id/available_products',
        u'/katello/api/organizations/:organization_id/sync_plans/:id/remove_products',
        u'/katello/api/sync_plans',
    ),
    u'sync': (
        u'/katello/api/organizations/:organization_id/products/:product_id/sync',
    ),
    u'system_errata': (
        u'/katello/api/systems/:system_id/errata/apply',
        u'/katello/api/systems/:system_id/errata/:id',
    ),
    u'system_packages': (
        u'/katello/api/systems/:system_id/packages/install',
        u'/katello/api/systems/:system_id/packages/remove',
        u'/katello/api/systems/:system_id/packages/upgrade_all',
    ),
    u'systems_bulk_actions': (
        u'/katello/api/systems/bulk/add_host_collections',
        u'/katello/api/systems/bulk/applicable_errata',
        u'/katello/api/systems/bulk/available_incremental_updates',
        u'/katello/api/systems/bulk/destroy',
        u'/katello/api/systems/bulk/environment_content_view',
        u'/katello/api/systems/bulk/install_content',
        u'/katello/api/systems/bulk/remove_content',
        u'/katello/api/systems/bulk/remove_host_collections',
        u'/katello/api/systems/bulk/update_content',
    ),
    u'systems': (
        u'/katello/api/environments/:environment_id/systems/report',
        u'/katello/api/systems',
        u'/katello/api/systems',
        u'/katello/api/systems/:id',
        u'/katello/api/systems/:id',
        u'/katello/api/systems/:id',
        u'/katello/api/systems/:id/available_host_collections',
        u'/katello/api/systems/:id/errata',
        u'/katello/api/systems/:id/events',
        u'/katello/api/systems/:id/packages',
        u'/katello/api/systems/:id/pools',
        u'/katello/api/systems/:id/refresh_subscriptions',
        u'/katello/api/systems/:id/releases',
    ),
    u'tasks': (
        u'/api/orchestration/:id/tasks',
    ),
    u'template_combinations': (
        u'/api/config_templates/:config_template_id/template_combinations',
        u'/api/config_templates/:config_template_id/template_combinations',
        u'/api/template_combinations/:id',
        u'/api/template_combinations/:id',
    ),
    u'template_kinds': (
        u'/api/template_kinds',
    ),
    u'uebercerts': (
        u'/katello/api/organizations/:organization_id/uebercert',
    ),
    u'usergroups': (
        u'/api/usergroups',
        u'/api/usergroups',
        u'/api/usergroups/:id',
        u'/api/usergroups/:id',
        u'/api/usergroups/:id',
    ),
    u'users': (
        u'/api/users',
        u'/api/users',
        u'/api/users/:id',
        u'/api/users/:id',
        u'/api/users/:id',
    ),
}


class TestAvailableURLs(TestCase):
    """Tests for ``api/v2``."""
    longMessage = True

    def setUp(self):
        """Define commonly-used variables."""
        self.path = '{0}/api/v2'.format(helpers.get_server_url())

    def test_get_status_code(self):
        """@Test: GET ``api/v2`` and examine the response.

        @Feature: API

        @Assert: HTTP 200 is returned with an ``application/json`` content-type

        """
        response = client.get(
            self.path,
            auth=helpers.get_server_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, httplib.OK)
        self.assertIn('application/json', response.headers['content-type'])

    @skip_if_bug_open('bugzilla', 1105773)
    def test_get_links(self):
        """@Test: GET ``api/v2`` and check the links returned.

        @Feature: API

        @Assert: The paths returned are equal to ``API_PATHS``.

        """
        # Did the server give us any paths at all?
        response = client.get(
            self.path,
            auth=helpers.get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()
        # See below for an explanation of this transformation.
        api_paths = response.json()['links']
        for group, path_pairs in api_paths.items():
            api_paths[group] = path_pairs.values()

        if bz_bug_is_open(1166875):
            # The server returns incorrect paths.
            api_paths['docker_images'].append(u'/katello/api/docker_images')
            api_paths['docker_images'].remove(u'/katello/api/compare')
            api_paths['docker_tags'].append(u'/katello/api/docker_tags')
            api_paths['docker_tags'].remove(u'/katello/api/compare')
            api_paths['errata'].append(u'/katello/api/errata')
            api_paths['errata'].append(u'/katello/api/errata/compare')
            api_paths['errata'].remove(u'/katello/api/compare')

        self.assertEqual(
            frozenset(api_paths.keys()),
            frozenset(API_PATHS.keys())
        )
        for group in api_paths.keys():
            if (
                    group == 'external_usergroups'
                    and bz_bug_is_open(1184170)
                    and get_distro_info()[1] == 7
            ):
                continue  # BZ 1184170 is open and affects the server.
            self.assertItemsEqual(api_paths[group], API_PATHS[group], group)

        # (line-too-long) pylint:disable=C0301
        # response.json()['links'] is a dict like this:
        #
        #     {u'content_views': {
        #          u'…': u'/katello/api/content_views/:id',
        #          u'…': u'/katello/api/content_views/:id/available_puppet_modules',
        #          u'…': u'/katello/api/organizations/:organization_id/content_views',
        #          u'…': u'/katello/api/organizations/:organization_id/content_views',
        #     }, …}
        #
        # We don't care about prose descriptions. It doesn't matter if those
        # change. Transform it before running any assertions:
        #
        #     {u'content_views': [
        #          u'/katello/api/content_views/:id',
        #          u'/katello/api/content_views/:id/available_puppet_modules',
        #          u'/katello/api/organizations/:organization_id/content_views',
        #          u'/katello/api/organizations/:organization_id/content_views',
        #     ], …}


class TestSmoke(TestCase):
    """End-to-end tests using the ``API`` path."""

    def test_find_default_org(self):
        """@Test: Check if 'Default Organization' is present

        @Feature: Smoke Test

        @Assert: 'Default Organization' is found

        """
        query = 'name="{0}"'.format(DEFAULT_ORG)
        results = self._search(entities.Organization, query)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], DEFAULT_ORG)

    def test_find_default_location(self):
        """@Test: Check if 'Default Location' is present

        @Feature: Smoke Test

        @Assert: 'Default Location' is found

        """
        query = 'name="{0}"'.format(DEFAULT_LOC)
        results = self._search(entities.Location, query)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], DEFAULT_LOC)

    def test_find_admin_user(self):
        """@Test: Check if Admin User is present

        @Feature: Smoke Test

        @Assert: Admin User is found and has Admin role

        """
        results = self._search(entities.User, 'login=admin')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['login'], 'admin')

    def test_ping(self):
        """@Test: Check if all services are running

        @Feature: Smoke Test

        @Assert: Overall and individual services status should be 'ok'.

        """
        response = client.get(
            entities.Ping().path(),
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()
        self.assertEqual(response.json()['status'], u'ok')  # overall status

        # Check that all services are OK. ['services'] is in this format:
        #
        # {u'services': {
        #    u'candlepin': {u'duration_ms': u'40', u'status': u'ok'},
        #    u'candlepin_auth': {u'duration_ms': u'41', u'status': u'ok'},
        #    …
        # }, u'status': u'ok'}
        services = response.json()['services']
        self.assertTrue(
            all([service['status'] == u'ok' for service in services.values()]),
            u"Not all services seem to be up and running!"
        )

    # FIXME: This test is still being developed and is not complete yet.
    def test_smoke(self):
        """@Test: Check that basic content can be created

        1. Create a new user with admin permissions
        2. Using the new user from above:
            1. Create a new organization
            2. Create two new lifecycle environments
            3. Create a custom product
            4. Create a custom YUM repository
            5. Create a custom PUPPET repository
            6. Synchronize both custom repositories
            7. Create a new content view
            8. Associate both repositories to new content view
            9. Publish content view
            10. Promote content view to both lifecycles
            11. Create a new libvirt compute resource
            12. Create a new subnet
            13. Create a new domain
            14. Create a new hostgroup and associate previous entities to it

        @Feature: Smoke Test

        @Assert: All entities are created and associated.

        """
        # prep work
        #
        # FIXME: Use a larger charset when authenticating users.
        #
        # It is possible to create a user with a wide range of characters. (see
        # the "User" entity). However, Foreman supports only HTTP Basic
        # authentication, and the requests lib enforces the latin1 charset in
        # this auth mode. We then further restrict ourselves to the
        # alphanumeric charset, because Foreman complains about incomplete
        # multi-byte chars when latin1 chars are used.
        #
        login = gen_string('alphanumeric')
        password = gen_string('alphanumeric')

        # step 1: Create a new user with admin permissions
        entities.User(admin=True, login=login, password=password).create()

        # step 2.1: Create a new organization
        org = entities.Organization().create(auth=(login, password))

        # step 2.2: Create 2 new lifecycle environments
        le1 = entities.LifecycleEnvironment(organization=org['id']).create()
        le2 = entities.LifecycleEnvironment(
            organization=org['id'], prior=le1['id']).create()

        # step 2.3: Create a custom product
        prod = entities.Product(organization=org['id']).create()

        # step 2.4: Create custom YUM repository
        repo1 = entities.Repository(
            product=prod['id'],
            content_type=u'yum',
            url=GOOGLE_CHROME_REPO
        ).create()

        # step 2.5: Create custom PUPPET repository
        repo2 = entities.Repository(
            product=prod['id'],
            content_type=u'puppet',
            url=FAKE_0_PUPPET_REPO
        ).create()

        # step 2.6: Synchronize both repositories
        for repo in [repo1, repo2]:
            response = client.post(
                entities.Repository(id=repo['id']).path('sync'),
                {
                    u'ids': [repo['id']],
                    u'organization_id': org['id']
                },
                auth=get_server_credentials(),
                verify=False,
            ).json()
            self.assertGreater(
                len(response['id']),
                1,
                u"Was not able to fetch a task ID.")
            task_status = entities.ForemanTask(id=response['id']).poll()
            self.assertEqual(
                task_status['result'],
                u'success',
                u"Sync for repository {0} failed.".format(repo['name']))

        # step 2.7: Create content view
        content_view = entities.ContentView(organization=org['id']).create()

        # step 2.8: Associate YUM repository to new content view
        response = client.put(
            entities.ContentView(id=content_view['id']).path(),
            auth=get_server_credentials(),
            verify=False,
            data={u'repository_ids': [repo1['id']]})

        # Fetch all available puppet modules
        puppet_mods = client.get(
            entities.ContentView(id=content_view['id']).path(
                'available_puppet_module_names'),
            auth=get_server_credentials(),
            verify=False).json()
        self.assertGreater(
            puppet_mods['results'],
            0,
            u"No puppet modules were found")

        # Select a random puppet module from the results
        puppet_mod = random.choice(puppet_mods['results'])
        # ... and associate it to the content view
        path = entities.ContentView(id=content_view['id']).path(
            'content_view_puppet_modules')
        response = client.post(
            path,
            auth=get_server_credentials(),
            verify=False,
            data={u'name': puppet_mod['module_name']})
        self.assertEqual(
            response.status_code,
            httplib.OK,
            status_code_error(path, httplib.OK, response)
        )
        self.assertEqual(
            response.json()['name'],
            puppet_mod['module_name'],
        )

        # step 2.9: Publish content view
        task_status = entities.ContentView(id=content_view['id']).publish()
        self.assertEqual(
            task_status['result'],
            u'success',
            u"Publishing {0} failed.".format(content_view['name']))

        # step 2.10: Promote content view to both lifecycles
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(
            len(content_view['versions']),
            1,
            u'There should only be 1 version published.')
        self.assertEqual(
            len(content_view['versions'][0]['environment_ids']),
            1,
            u"Content view should be present on 1 lifecycle only")
        task_status = entities.ContentViewVersion(
            id=content_view['versions'][0]['id']
        ).promote(le1['id'])
        self.assertEqual(
            task_status['result'],
            u'success',
            u"Promoting {0} to {1} failed.".format(
                content_view['name'], le1['name']))
        # Check that content view exists in 2 lifecycles
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(
            len(content_view['versions']),
            1,
            u'There should only be 1 version published.')
        self.assertEqual(
            len(content_view['versions'][0]['environment_ids']),
            2,
            u"Content view should be present on 2 lifecycles only")
        task_status = entities.ContentViewVersion(
            id=content_view['versions'][0]['id']
        ).promote(le2['id'])
        self.assertEqual(
            task_status['result'],
            u'success',
            u"Promoting {0} to {1} failed.".format(
                content_view['name'], le2['name']))
        # Check that content view exists in 2 lifecycles
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(
            len(content_view['versions']),
            1,
            u'There should only be 1 version published.')
        self.assertEqual(
            len(content_view['versions'][0]['environment_ids']),
            3,
            u"Content view should be present on 3 lifecycle only")

        # BONUS: Create a content host and associate it with promoted
        # content view and last lifecycle where it exists
        content_host = entities.System(
            content_view=content_view['id'],
            environment=le2['id']
        ).create()
        # Check that content view matches what we passed
        self.assertEqual(
            content_host['content_view_id'],
            content_view['id'],
            u"Content views do not match."
        )
        # Check that lifecycle environment matches
        self.assertEqual(
            content_host['environment']['id'],
            le2['id'],
            u"Environments do not match."
        )

    def _search(self, entity, query, auth=None):
        """Performs a GET ``api/v2/<entity>`` and specify the ``search``
        parameter.

        :param robottelo.orm.Entity entity: A logical representation of a
            Foreman entity.
        :param string query: A ``search`` parameter.
        :param tuple auth: A ``tuple`` containing the credentials to be used
            for authentication when accessing the API. If ``None``,
            credentials are automatically read from
            :func:`robottelo.common.helpers.get_server_credentials`.
        :return: A ``list`` of found entity dicts or an empty list if nothing
            found
        :rtype: list

        """
        # Use the server credentials if None are provided
        if auth is None:
            auth = get_server_credentials()

        path = entity().path()
        response = client.get(
            path,
            auth=auth,
            data={u'search': query},
            verify=False,
        )
        response.raise_for_status()
        return response.json()['results']

    def test_end_to_end(self):
        """@Test: Perform end to end smoke tests using RH repos.

        1. Create new organization and environment
        2. Clone and upload manifest
        3. Sync a RedHat repository
        4. Create content-view
        5. Add repository to contet-view
        6. Promote/publish content-view
        7. Create an activation-key
        8. Add product to activation-key
        9. Create new virtualmachine
        10. Pull rpm from Foreman server and install on client
        11. Register client with foreman server using activation-key
        12. Install rpm on client

        @Feature: Smoke test

        @Assert: All tests should succeed and Content should be successfully
        fetched by client

        """
        product = "Red Hat Enterprise Linux Server"
        reposet = ("Red Hat Enterprise Virtualization Agents "
                   "for RHEL 6 Server (RPMs)")
        repo = ("Red Hat Enterprise Virtualization Agents for RHEL 6 Server "
                "RPMs x86_64 6Server")
        activation_key_name = gen_string('alpha')

        # step 1.1: Create a new organization
        org = entities.Organization().create()

        # step 1.2: Create new lifecycle environments
        lifecycle_env = entities.LifecycleEnvironment(
            organization=org['id']
        ).create()

        # step 2: Upload manifest
        manifest_path = manifests.clone()
        task = entities.Organization(
            id=org['id']
        ).upload_manifest(path=manifest_path)
        self.assertEqual(
            u'success', task['result'], task['humanized']['errors']
        )
        # step 3.1: Enable RH repo and fetch repository_id
        repo_id = utils.enable_rhrepo_and_fetchid(
            basearch="x86_64",
            org_id=org['id'],
            product=product,
            repo=repo,
            reposet=reposet,
            releasever="6Server",
        )
        # step 3.2: sync repository
        task_result = entities.Repository(id=repo_id).sync()['result']
        self.assertEqual(
            task_result,
            u'success',
            u" Error while syncing repository '{0}' and state is {1}."
            .format(repo, task_result))

        # step 4: Create content view
        content_view = entities.ContentView(organization=org['id']).create()
        # step 5: Associate repository to new content view
        response = client.put(
            entities.ContentView(id=content_view['id']).path(),
            {u'repository_ids': [repo_id]},
            auth=get_server_credentials(),
            verify=False,
        )
        response.raise_for_status()

        # step 6.1: Publish content view
        task_status = entities.ContentView(id=content_view['id']).publish()
        self.assertEqual(
            task_status['result'],
            u'success',
            u"Error publishing content-view {0} and state is {1}."
            .format(content_view['name'], task_status['result']))

        # step 6.2: Promote content view to lifecycle_env
        content_view = entities.ContentView(id=content_view['id']).read_json()
        self.assertEqual(len(content_view['versions']), 1)
        task_status = entities.ContentViewVersion(
            id=content_view['versions'][0]['id']
        ).promote(lifecycle_env['id'])
        self.assertEqual(
            task_status['result'],
            u'success',
            u"Error promoting {0} to {1} and state is {2}."
            .format(content_view['name'],
                    lifecycle_env['name'],
                    task_status['result']))

        # step 7: Create activation key
        ak_id = entities.ActivationKey(
            name=activation_key_name,
            environment=lifecycle_env['id'],
            organization=org['id'],
            content_view=content_view['id'],
        ).create_json()['id']

        # Walk through the list of subscriptions. Find the "Red Hat Employee
        # Subscription" and attach it to the just-created activation key.
        for subscription in entities.Organization(id=org['id']).subscriptions():
            if subscription['product_name'] == "Red Hat Employee Subscription":
                # 'quantity' must be 1, not subscription['quantity']. Greater
                # values produce this error: "RuntimeError: Error: Only pools
                # with multi-entitlement product subscriptions can be added to
                # the activation key with a quantity greater than one."
                entities.ActivationKey(id=ak_id).add_subscriptions({
                    'quantity': 1,
                    'subscription_id': subscription['id'],
                })
                break

        # Create VM
        package_name = "python-kitchen"
        with VirtualMachine(distro='rhel66') as vm:
            # Download and Install rpm
            result = vm.run(
                "wget -nd -r -l1 --no-parent -A '*.noarch.rpm' http://{0}/pub/"
                .format(conf.properties['main.server.hostname'])
            )
            self.assertEqual(
                result.return_code, 0,
                "failed to fetch katello-ca rpm: {0}, return code: {1}"
                .format(result.stderr, result.return_code)
            )
            result = vm.run(
                'rpm -i katello-ca-consumer*.noarch.rpm'
            )
            self.assertEqual(
                result.return_code, 0,
                "failed to install katello-ca rpm: {0} and return code: {1}"
                .format(result.stderr, result.return_code)
            )
            # Register client with foreman server using activation-key
            result = vm.run(
                u'subscription-manager register --activationkey {0} '
                '--org {1} --force'
                .format(activation_key_name, org['label'])
            )
            self.assertEqual(
                result.return_code, 0,
                "failed to register client:: {0} and return code: {1}"
                .format(result.stderr, result.return_code)
            )
            # Enable Red Hat Enterprise Virtualization Agents repo via cli
            # As the below repo is disabled by default under ak's prd-content
            result = vm.run(
                'subscription-manager repos --enable '
                'rhel-6-server-rhev-agent-rpms'
            )
            self.assertEqual(
                result.return_code, 0,
                "Enabling repo failed: {0} and return code: {1}"
                .format(result.stderr, result.return_code)
            )
            # Install contents from sat6 server
            result = vm.run('yum install -y {0}'.format(package_name))
            self.assertEqual(
                result.return_code, 0,
                "Package install failed: {0} and return code: {1}"
                .format(result.stderr, result.return_code)
            )
            # Verify if package is installed by query it
            result = vm.run('rpm -q {0}'.format(package_name))
            self.assertIn(package_name, result.stdout[0])
