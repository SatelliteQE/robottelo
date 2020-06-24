# coding=utf-8
"""Smoke tests for the ``API`` end-to-end scenario.

:Requirement: Api Endtoend

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import http
import random

import pytest
from fauxfactory import gen_string
from nailgun import client
from nailgun import entities

from .utils import AK_CONTENT_LABEL
from .utils import ClientProvisioningMixin
from robottelo import manifests
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.api.utils import promote
from robottelo.api.utils import upload_manifest
from robottelo.config import settings
from robottelo.constants import CUSTOM_RPM_REPO
from robottelo.constants import DEFAULT_LOC
from robottelo.constants import DEFAULT_ORG
from robottelo.constants import DEFAULT_SUBSCRIPTION_NAME
from robottelo.constants import FAKE_0_PUPPET_REPO
from robottelo.constants import PRDS
from robottelo.constants import REPOS
from robottelo.constants import REPOSET
from robottelo.decorators import setting_is_set
from robottelo.decorators import skip_if_not_set
from robottelo.decorators import tier1
from robottelo.decorators import tier4
from robottelo.decorators import upgrade
from robottelo.helpers import get_nailgun_config
from robottelo.test import TestCase

API_PATHS = {
    # flake8:noqa (line-too-long)
    'activation_keys': (
        '/katello/api/activation_keys',
        '/katello/api/activation_keys',
        '/katello/api/activation_keys/:id',
        '/katello/api/activation_keys/:id',
        '/katello/api/activation_keys/:id',
        '/katello/api/activation_keys/:id/add_subscriptions',
        '/katello/api/activation_keys/:id/content_override',
        '/katello/api/activation_keys/:id/copy',
        '/katello/api/activation_keys/:id/host_collections/available',
        '/katello/api/activation_keys/:id/product_content',
        '/katello/api/activation_keys/:id/releases',
        '/katello/api/activation_keys/:id/remove_subscriptions',
    ),
    'ansible_collections': (
        '/katello/api/ansible_collections/compare',
        '/katello/api/ansible_collections/:id',
    ),
    'ansible_inventories': (
        '/api/ansible_inventories/hosts',
        '/api/ansible_inventories/schedule',
    ),
    'ansible_override_values': (
        '/ansible/api/ansible_override_values',
        '/ansible/api/ansible_override_values/:id',
    ),
    'ansible_roles': (
        '/ansible/api/ansible_roles',
        '/ansible/api/ansible_roles/:id',
        '/ansible/api/ansible_roles/:id',
        '/ansible/api/ansible_roles/fetch',
        '/ansible/api/ansible_roles/import',
        '/ansible/api/ansible_roles/obsolete',
    ),
    'ansible_variables': (
        '/ansible/api/ansible_variables/:id',
        '/ansible/api/ansible_variables',
        '/ansible/api/ansible_variables/:id',
        '/ansible/api/ansible_variables',
        '/ansible/api/ansible_variables/:id',
        '/ansible/api/ansible_variables/import',
        '/ansible/api/ansible_variables/obsolete',
    ),
    'api': (),
    'architectures': (
        '/api/architectures',
        '/api/architectures',
        '/api/architectures/:id',
        '/api/architectures/:id',
        '/api/architectures/:id',
    ),
    'arf_reports': (
        '/api/compliance/arf/:cname/:policy_id/:date',
        '/api/compliance/arf_reports',
        '/api/compliance/arf_reports/:id',
        '/api/compliance/arf_reports/:id',
        '/api/compliance/arf_reports/:id/download',
        '/api/compliance/arf_reports/:id/download_html',
    ),
    'audits': ('/api/audits', '/api/audits/:id'),
    'auth_source_externals': (
        '/api/auth_source_externals',
        '/api/auth_source_externals/:id',
        '/api/auth_source_externals/:id',
    ),
    'auth_source_internals': ('/api/auth_source_internals', '/api/auth_source_internals/:id'),
    'auth_source_ldaps': (
        '/api/auth_source_ldaps',
        '/api/auth_source_ldaps',
        '/api/auth_source_ldaps/:id',
        '/api/auth_source_ldaps/:id',
        '/api/auth_source_ldaps/:id',
        '/api/auth_source_ldaps/:id/test',
    ),
    'auth_sources': ('/api/auth_sources',),
    'autosign': (
        '/api/smart_proxies/:smart_proxy_id/autosign',
        '/api/smart_proxies/:smart_proxy_id/autosign',
        '/api/smart_proxies/:smart_proxy_id/autosign/:id',
    ),
    'base': (),
    'bookmarks': (
        '/api/bookmarks',
        '/api/bookmarks',
        '/api/bookmarks/:id',
        '/api/bookmarks/:id',
        '/api/bookmarks/:id',
    ),
    'candlepin_dynflow_proxy': (
        '/katello/api/consumers/:id/profiles',
        '/katello/api/systems/:id/deb_package_profile',
    ),
    'candlepin_proxies': (
        '/katello/api/consumers/:id/tracer',
        '/katello/api/systems/:id/enabled_repos',
    ),
    'capsule_content': (
        '/katello/api/capsules/:id/content/available_lifecycle_environments',
        '/katello/api/capsules/:id/content/lifecycle_environments',
        '/katello/api/capsules/:id/content/lifecycle_environments',
        '/katello/api/capsules/:id/content/lifecycle_environments/:environment_id',
        '/katello/api/capsules/:id/content/sync',
        '/katello/api/capsules/:id/content/sync',
        '/katello/api/capsules/:id/content/sync',
    ),
    'capsules': ('/katello/api/capsules', '/katello/api/capsules/:id'),
    'common_parameters': (
        '/api/common_parameters',
        '/api/common_parameters',
        '/api/common_parameters/:id',
        '/api/common_parameters/:id',
        '/api/common_parameters/:id',
    ),
    'compute_attributes': (
        '/api/compute_resources/:compute_resource_id/compute_profiles/:compute_profile_id/compute_attributes',
        '/api/compute_resources/:compute_resource_id/compute_profiles/:compute_profile_id/compute_attributes/:id',
        '/api/compute_resources/:compute_resource_id/compute_profiles/:compute_profile_id/compute_attributes',
        '/api/compute_resources/:compute_resource_id/compute_profiles/:compute_profile_id/compute_attributes/:id',
    ),
    'compute_profiles': (
        '/api/compute_profiles',
        '/api/compute_profiles',
        '/api/compute_profiles/:id',
        '/api/compute_profiles/:id',
        '/api/compute_profiles/:id',
    ),
    'compute_resources': (
        '/api/compute_resources',
        '/api/compute_resources',
        '/api/compute_resources/:id',
        '/api/compute_resources/:id',
        '/api/compute_resources/:id',
        '/api/compute_resources/:id/associate',
        '/api/compute_resources/:id/available_clusters',
        '/api/compute_resources/:id/available_clusters/:cluster_id/available_resource_pools',
        '/api/compute_resources/:id/available_flavors',
        '/api/compute_resources/:id/available_folders',
        '/api/compute_resources/:id/available_images',
        '/api/compute_resources/:id/available_networks',
        '/api/compute_resources/:id/available_security_groups',
        '/api/compute_resources/:id/available_storage_domains',
        '/api/compute_resources/:id/available_storage_pods',
        '/api/compute_resources/:id/available_zones',
        '/api/compute_resources/:id/refresh_cache',
        '/api/compute_resources/:id/storage_domains/:storage_domain_id',
        '/api/compute_resources/:id/storage_pods/:storage_pod_id',
    ),
    'configs': (
        '/foreman_virt_who_configure/api/v2/configs',
        '/foreman_virt_who_configure/api/v2/configs',
        '/foreman_virt_who_configure/api/v2/configs/:id',
        '/foreman_virt_who_configure/api/v2/configs/:id',
        '/foreman_virt_who_configure/api/v2/configs/:id',
        '/foreman_virt_who_configure/api/v2/configs/:id/deploy_script',
    ),
    'config_groups': (
        '/api/config_groups',
        '/api/config_groups',
        '/api/config_groups/:id',
        '/api/config_groups/:id',
        '/api/config_groups/:id',
    ),
    'config_reports': (
        '/api/config_reports',
        '/api/config_reports',
        '/api/config_reports/:id',
        '/api/config_reports/:id',
        '/api/hosts/:host_id/config_reports/last',
    ),
    'content_credentials': (
        '/katello/api/content_credentials',
        '/katello/api/content_credentials',
        '/katello/api/content_credentials/:id',
        '/katello/api/content_credentials/:id',
        '/katello/api/content_credentials/:id',
        '/katello/api/content_credentials/:id/content',
        '/katello/api/content_credentials/:id/content',
    ),
    'content_uploads': (
        '/katello/api/repositories/:repository_id/content_uploads',
        '/katello/api/repositories/:repository_id/content_uploads/:id',
        '/katello/api/repositories/:repository_id/content_uploads/:id',
    ),
    'content_view_components': (
        '/katello/api/content_views/:composite_content_view_id/content_view_components',
        '/katello/api/content_views/:composite_content_view_id/content_view_components/:id',
        '/katello/api/content_views/:composite_content_view_id/content_view_components/:id',
        '/katello/api/content_views/:composite_content_view_id/content_view_components/add',
        '/katello/api/content_views/:composite_content_view_id/content_view_components/remove',
    ),
    'content_view_filter_rules': (
        '/katello/api/content_view_filters/:content_view_filter_id/rules',
        '/katello/api/content_view_filters/:content_view_filter_id/rules',
        '/katello/api/content_view_filters/:content_view_filter_id/rules/:id',
        '/katello/api/content_view_filters/:content_view_filter_id/rules/:id',
        '/katello/api/content_view_filters/:content_view_filter_id/rules/:id',
    ),
    'content_view_filters': (
        '/katello/api/content_views/:content_view_id/filters',
        '/katello/api/content_views/:content_view_id/filters',
        '/katello/api/content_views/:content_view_id/filters/:id',
        '/katello/api/content_views/:content_view_id/filters/:id',
        '/katello/api/content_views/:content_view_id/filters/:id',
    ),
    'content_view_puppet_modules': (
        '/katello/api/content_views/:content_view_id/content_view_puppet_modules',
        '/katello/api/content_views/:content_view_id/content_view_puppet_modules',
        '/katello/api/content_views/:content_view_id/content_view_puppet_modules/:id',
        '/katello/api/content_views/:content_view_id/content_view_puppet_modules/:id',
        '/katello/api/content_views/:content_view_id/content_view_puppet_modules/:id',
    ),
    'content_views': (
        '/katello/api/content_views/:id',
        '/katello/api/content_views/:id',
        '/katello/api/content_views/:id',
        '/katello/api/content_views/:id/available_puppet_module_names',
        '/katello/api/content_views/:id/available_puppet_modules',
        '/katello/api/content_views/:id/copy',
        '/katello/api/content_views/:id/environments/:environment_id',
        '/katello/api/content_views/:id/publish',
        '/katello/api/content_views/:id/remove',
        '/katello/api/organizations/:organization_id/content_views',
        '/katello/api/organizations/:organization_id/content_views',
    ),
    'content_view_histories': ('/katello/api/content_views/:id/history',),
    'content_view_versions': (
        '/katello/api/content_view_versions',
        '/katello/api/content_view_versions/:id',
        '/katello/api/content_view_versions/:id',
        '/katello/api/content_view_versions/:id',
        '/katello/api/content_view_versions/:id/export',
        '/katello/api/content_view_versions/:id/promote',
        '/katello/api/content_view_versions/:id/republish_repositories',
        '/katello/api/content_view_versions/incremental_update',
    ),
    'dashboard': ('/api/dashboard',),
    'debs': ('/katello/api/debs/:id', '/katello/api/debs/compare'),
    'discovered_hosts': (
        '/api/v2/discovered_hosts',
        '/api/v2/discovered_hosts',
        '/api/v2/discovered_hosts/:id',
        '/api/v2/discovered_hosts/:id',
        '/api/v2/discovered_hosts/:id',
        '/api/v2/discovered_hosts/:id/auto_provision',
        '/api/v2/discovered_hosts/:id/reboot',
        '/api/v2/discovered_hosts/:id/refresh_facts',
        '/api/v2/discovered_hosts/auto_provision_all',
        '/api/v2/discovered_hosts/facts',
        '/api/v2/discovered_hosts/reboot_all',
    ),
    'discovery_rules': (
        '/api/v2/discovery_rules',
        '/api/v2/discovery_rules',
        '/api/v2/discovery_rules/:id',
        '/api/v2/discovery_rules/:id',
        '/api/v2/discovery_rules/:id',
    ),
    'disks': ('/bootdisk/api', '/bootdisk/api/generic', '/bootdisk/api/hosts/:host_id'),
    'docker_manifests': (
        '/katello/api/docker_manifests/:id',
        '/katello/api/docker_manifests/compare',
    ),
    'docker_manifest_lists': (
        '/katello/api/docker_manifest_lists/:id',
        '/katello/api/docker_manifest_lists/compare',
    ),
    'docker_tags': ('/katello/api/docker_tags/compare', '/katello/api/docker_tags/:id'),
    'domains': (
        '/api/domains',
        '/api/domains',
        '/api/domains/:id',
        '/api/domains/:id',
        '/api/domains/:id',
    ),
    'environments': (
        '/api/environments',
        '/api/environments',
        '/api/environments/:id',
        '/api/environments/:id',
        '/api/environments/:id',
        '/api/smart_proxies/:id/import_puppetclasses',
    ),
    'errata': (
        '/katello/api/content_view_versions/:id/available_errata',
        '/katello/api/errata/compare',
        '/katello/api/errata/:id',
    ),
    'external_usergroups': (
        '/api/usergroups/:usergroup_id/external_usergroups',
        '/api/usergroups/:usergroup_id/external_usergroups',
        '/api/usergroups/:usergroup_id/external_usergroups/:id',
        '/api/usergroups/:usergroup_id/external_usergroups/:id',
        '/api/usergroups/:usergroup_id/external_usergroups/:id',
        '/api/usergroups/:usergroup_id/external_usergroups/:id/refresh',
    ),
    'fact_values': ('/api/fact_values',),
    'file_units': ('/katello/api/files/compare', '/katello/api/files/:id'),
    'filters': (
        '/api/filters',
        '/api/filters',
        '/api/filters/:id',
        '/api/filters/:id',
        '/api/filters/:id',
    ),
    'foreign_input_sets': (
        '/api/templates/:template_id/foreign_input_sets',
        '/api/templates/:template_id/foreign_input_sets',
        '/api/templates/:template_id/foreign_input_sets/:id',
        '/api/templates/:template_id/foreign_input_sets/:id',
        '/api/templates/:template_id/foreign_input_sets/:id',
    ),
    'foreman_tasks': (
        '/foreman_tasks/api/tasks',
        '/foreman_tasks/api/tasks/:id',
        '/foreman_tasks/api/tasks/:id/details',
        '/foreman_tasks/api/tasks/:id/sub_tasks',
        '/foreman_tasks/api/tasks/bulk_resume',
        '/foreman_tasks/api/tasks/bulk_search',
        '/foreman_tasks/api/tasks/callback',
        '/foreman_tasks/api/tasks/summary',
    ),
    'gpg_keys': (
        '/katello/api/gpg_keys',
        '/katello/api/gpg_keys',
        '/katello/api/gpg_keys/:id',
        '/katello/api/gpg_keys/:id',
        '/katello/api/gpg_keys/:id',
        '/katello/api/gpg_keys/:id/content',
        '/katello/api/gpg_keys/:id/content',
    ),
    'home': ('/api', '/api/status'),
    'host_autocomplete': (),
    'host_classes': (
        '/api/hosts/:host_id/puppetclass_ids',
        '/api/hosts/:host_id/puppetclass_ids',
        '/api/hosts/:host_id/puppetclass_ids/:id',
    ),
    'host_collections': (
        '/katello/api/host_collections',
        '/katello/api/host_collections',
        '/katello/api/host_collections/:id',
        '/katello/api/host_collections/:id',
        '/katello/api/host_collections/:id',
        '/katello/api/host_collections/:id/add_hosts',
        '/katello/api/host_collections/:id/copy',
        '/katello/api/host_collections/:id/remove_hosts',
    ),
    'host_debs': ('/api/hosts/:host_id/debs',),
    'host_module_streams': ('/api/hosts/:host_id/module_streams',),
    'host_subscriptions': (
        '/api/hosts/:host_id/subscriptions',
        '/api/hosts/:host_id/subscriptions',
        '/api/hosts/:host_id/subscriptions/add_subscriptions',
        '/api/hosts/:host_id/subscriptions/auto_attach',
        '/api/hosts/:host_id/subscriptions/available_release_versions',
        '/api/hosts/:host_id/subscriptions/content_override',
        '/api/hosts/:host_id/subscriptions/events',
        '/api/hosts/:host_id/subscriptions/product_content',
        '/api/hosts/subscriptions',
    ),
    'host_tracer': ('/api/hosts/:host_id/traces',),
    'hostgroup_classes': (
        '/api/hostgroups/:hostgroup_id/puppetclass_ids',
        '/api/hostgroups/:hostgroup_id/puppetclass_ids',
        '/api/hostgroups/:hostgroup_id/puppetclass_ids/:id',
    ),
    'hostgroups': (
        '/api/hostgroups',
        '/api/hostgroups/:id',
        '/api/hostgroups',
        '/api/hostgroups/:id',
        '/api/hostgroups/:id',
        '/api/hostgroups/:id/clone',
        '/api/hostgroups/:id/rebuild_config',
        '/api/hostgroups/:id/play_roles',
        '/api/hostgroups/multiple_play_roles',
        '/api/hostgroups/:id/ansible_roles',
        '/api/hostgroups/:id/assign_ansible_roles',
    ),
    'hosts': (
        '/api/hosts',
        '/api/hosts/:id',
        '/api/hosts',
        '/api/hosts/:id',
        '/api/hosts/:id',
        '/api/hosts/:id/enc',
        '/api/hosts/:id/status',
        '/api/hosts/:id/status/:type',
        '/api/hosts/:id/vm_compute_attributes',
        '/api/hosts/:id/disassociate',
        '/api/hosts/:id/power',
        '/api/hosts/:id/power',
        '/api/hosts/:id/boot',
        '/api/hosts/facts',
        '/api/hosts/:id/rebuild_config',
        '/api/hosts/:id/template/:kind',
        '/api/hosts/:id/play_roles',
        '/api/hosts/multiple_play_roles',
        '/api/hosts/:id/ansible_roles',
        '/api/hosts/:id/assign_ansible_roles',
        '/api/hosts/:host_id/host_collections',
        '/api/hosts/:id/policies_enc',
    ),
    'hosts_bulk_actions': (
        '/api/hosts/bulk/add_host_collections',
        '/api/hosts/bulk/add_subscriptions',
        '/api/hosts/bulk/auto_attach',
        '/api/hosts/bulk/applicable_errata',
        '/api/hosts/bulk/available_incremental_updates',
        '/api/hosts/bulk/content_overrides',
        '/api/hosts/bulk/destroy',
        '/api/hosts/bulk/environment_content_view',
        '/api/hosts/bulk/install_content',
        '/api/hosts/bulk/installable_errata',
        '/api/hosts/bulk/module_streams',
        '/api/hosts/bulk/release_version',
        '/api/hosts/bulk/remove_content',
        '/api/hosts/bulk/remove_host_collections',
        '/api/hosts/bulk/remove_subscriptions',
        '/api/hosts/bulk/update_content',
    ),
    'host_errata': (
        '/api/hosts/:host_id/errata',
        '/api/hosts/:host_id/errata/:id',
        '/api/hosts/:host_id/errata/applicability',
        '/api/hosts/:host_id/errata/apply',
    ),
    'host_packages': (
        '/api/hosts/:host_id/packages',
        '/api/hosts/:host_id/packages/install',
        '/api/hosts/:host_id/packages/remove',
        '/api/hosts/:host_id/packages/upgrade_all',
    ),
    'http_proxies': (
        '/api/http_proxies',
        '/api/http_proxies',
        '/api/http_proxies/:id',
        '/api/http_proxies/:id',
        '/api/http_proxies/:id',
    ),
    'images': (
        '/api/compute_resources/:compute_resource_id/images',
        '/api/compute_resources/:compute_resource_id/images',
        '/api/compute_resources/:compute_resource_id/images/:id',
        '/api/compute_resources/:compute_resource_id/images/:id',
        '/api/compute_resources/:compute_resource_id/images/:id',
    ),
    'interfaces': (
        '/api/hosts/:host_id/interfaces',
        '/api/hosts/:host_id/interfaces',
        '/api/hosts/:host_id/interfaces/:id',
        '/api/hosts/:host_id/interfaces/:id',
        '/api/hosts/:host_id/interfaces/:id',
    ),
    'job_invocations': (
        '/api/job_invocations',
        '/api/job_invocations',
        '/api/job_invocations/:id',
        '/api/job_invocations/:id/cancel',
        '/api/job_invocations/:id/hosts/:host_id',
        '/api/job_invocations/:id/hosts/:host_id/raw',
        '/api/job_invocations/:id/rerun',
    ),
    'job_templates': (
        '/api/job_templates',
        '/api/job_templates',
        '/api/job_templates/:id',
        '/api/job_templates/:id',
        '/api/job_templates/:id',
        '/api/job_templates/:id/clone',
        '/api/job_templates/:id/export',
        '/api/job_templates/import',
    ),
    'lifecycle_environments': (
        '/katello/api/environments',
        '/katello/api/environments',
        '/katello/api/environments/:id',
        '/katello/api/environments/:id',
        '/katello/api/environments/:id',
        '/katello/api/organizations/:organization_id/environments/paths',
    ),
    'locations': (
        '/api/locations',
        '/api/locations',
        '/api/locations/:id',
        '/api/locations/:id',
        '/api/locations/:id',
    ),
    'mail_notifications': ('/api/mail_notifications', '/api/mail_notifications/:id'),
    'media': ('/api/media', '/api/media', '/api/media/:id', '/api/media/:id', '/api/media/:id',),
    'models': (
        '/api/models',
        '/api/models',
        '/api/models/:id',
        '/api/models/:id',
        '/api/models/:id',
    ),
    'module_streams': ('/katello/api/module_streams/compare', '/katello/api/module_streams/:id',),
    'operatingsystems': (
        '/api/operatingsystems',
        '/api/operatingsystems',
        '/api/operatingsystems/:id',
        '/api/operatingsystems/:id',
        '/api/operatingsystems/:id',
        '/api/operatingsystems/:id/bootfiles',
    ),
    'organizations': (
        '/katello/api/organizations',
        '/katello/api/organizations',
        '/katello/api/organizations/:id',
        '/katello/api/organizations/:id',
        '/katello/api/organizations/:id',
        '/katello/api/organizations/:id/autoattach_subscriptions',
        '/katello/api/organizations/:id/redhat_provider',
        '/katello/api/organizations/:id/releases',
        '/katello/api/organizations/:id/repo_discover',
        '/katello/api/organizations/:label/cancel_repo_discover',
        '/katello/api/organizations/:label/download_debug_certificate',
    ),
    'os_default_templates': (
        '/api/operatingsystems/:operatingsystem_id/os_default_templates',
        '/api/operatingsystems/:operatingsystem_id/os_default_templates',
        '/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
        '/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
        '/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
    ),
    'ostree_branches': (
        '/katello/api/ostree_branches/:id',
        '/katello/api/ostree_branches/compare',
    ),
    'override_values': (
        '/api/smart_variables/:smart_variable_id/override_values',
        '/api/smart_variables/:smart_variable_id/override_values',
        '/api/smart_variables/:smart_variable_id/override_values/:id',
        '/api/smart_variables/:smart_variable_id/override_values/:id',
        '/api/smart_variables/:smart_variable_id/override_values/:id',
    ),
    'package_groups': (
        '/katello/api/package_group',
        '/katello/api/package_group',
        '/katello/api/package_groups/:id',
        '/katello/api/package_groups/compare',
    ),
    'packages': ('/katello/api/packages/:id', '/katello/api/packages/compare'),
    'parameters': (
        '/api/hosts/:host_id/parameters',
        '/api/hosts/:host_id/parameters',
        '/api/hosts/:host_id/parameters',
        '/api/hosts/:host_id/parameters/:id',
        '/api/hosts/:host_id/parameters/:id',
        '/api/hosts/:host_id/parameters/:id',
    ),
    'permissions': (
        '/api/permissions',
        '/api/permissions/:id',
        '/api/permissions/resource_types',
    ),
    'personal_access_tokens': (
        '/api/users/:user_id/personal_access_tokens',
        '/api/users/:user_id/personal_access_tokens',
        '/api/users/:user_id/personal_access_tokens/:id',
        '/api/users/:user_id/personal_access_tokens/:id',
    ),
    'ping': ('/katello/api/ping', '/katello/api/status', '/api/ping', '/api/statuses'),
    'plugins': ('/api/plugins',),
    'policies': (
        '/api/compliance/policies',
        '/api/compliance/policies',
        '/api/compliance/policies/:id',
        '/api/compliance/policies/:id',
        '/api/compliance/policies/:id',
        '/api/compliance/policies/:id/content',
        '/api/compliance/policies/:id/tailoring',
    ),
    'products_bulk_actions': (
        '/katello/api/products/bulk/destroy',
        '/katello/api/products/bulk/http_proxy',
        '/katello/api/products/bulk/sync_plan',
    ),
    'products': (
        '/katello/api/products',
        '/katello/api/products',
        '/katello/api/products/:id',
        '/katello/api/products/:id',
        '/katello/api/products/:id',
        '/katello/api/products/:id/sync',
    ),
    'provisioning_templates': (
        '/api/provisioning_templates',
        '/api/provisioning_templates',
        '/api/provisioning_templates/:id',
        '/api/provisioning_templates/:id',
        '/api/provisioning_templates/:id',
        '/api/provisioning_templates/:id/clone',
        '/api/provisioning_templates/:id/export',
        '/api/provisioning_templates/build_pxe_default',
        '/api/provisioning_templates/import',
    ),
    'ptables': (
        '/api/ptables',
        '/api/ptables',
        '/api/ptables/:id',
        '/api/ptables/:id',
        '/api/ptables/:id',
        '/api/ptables/:id/clone',
        '/api/ptables/:id/export',
        '/api/ptables/import',
    ),
    'puppetclasses': (
        '/api/puppetclasses',
        '/api/puppetclasses',
        '/api/puppetclasses/:id',
        '/api/puppetclasses/:id',
        '/api/puppetclasses/:id',
    ),
    'puppet_hosts': ('/api/hosts/:id/puppetrun',),
    'puppet_modules': ('/katello/api/puppet_modules/compare', '/katello/api/puppet_modules/:id',),
    'realms': (
        '/api/realms',
        '/api/realms',
        '/api/realms/:id',
        '/api/realms/:id',
        '/api/realms/:id',
    ),
    'recurring_logics': (
        '/foreman_tasks/api/recurring_logics',
        '/foreman_tasks/api/recurring_logics/:id',
        '/foreman_tasks/api/recurring_logics/:id',
        '/foreman_tasks/api/recurring_logics/:id/cancel',
    ),
    'remote_execution_features': (
        '/api/remote_execution_features',
        '/api/remote_execution_features/:id',
        '/api/remote_execution_features/:id',
    ),
    'reports': (
        '/api/hosts/:host_id/reports/last',
        '/api/reports',
        '/api/reports',
        '/api/reports/:id',
        '/api/reports/:id',
    ),
    'report_templates': (
        '/api/report_templates',
        '/api/report_templates/:id',
        '/api/report_templates',
        '/api/report_templates/import',
        '/api/report_templates/:id',
        '/api/report_templates/:id',
        '/api/report_templates/:id/clone',
        '/api/report_templates/:id/export',
        '/api/report_templates/:id/generate',
        '/api/report_templates/:id/schedule_report',
        '/api/report_templates/:id/report_data/:job_id',
    ),
    'repositories_bulk_actions': (
        '/katello/api/repositories/bulk/destroy',
        '/katello/api/repositories/bulk/sync',
    ),
    'repositories': (
        '/katello/api/repositories',
        '/katello/api/repositories',
        '/katello/api/repositories/:id',
        '/katello/api/repositories/:id',
        '/katello/api/repositories/:id',
        '/katello/api/repositories/:id/export',
        '/katello/api/repositories/:id/gpg_key_content',
        '/katello/api/repositories/:id/import_uploads',
        '/katello/api/repositories/:id/republish',
        '/katello/api/repositories/:id/sync',
        '/katello/api/repositories/:id/upload_content',
        '/katello/api/repositories/repository_types',
    ),
    'repository_sets': (
        '/katello/api/repository_sets',
        '/katello/api/repository_sets/:id',
        '/katello/api/repository_sets/:id/available_repositories',
        '/katello/api/repository_sets/:id/disable',
        '/katello/api/repository_sets/:id/enable',
    ),
    'roles': (
        '/api/roles',
        '/api/roles',
        '/api/roles/:id',
        '/api/roles/:id',
        '/api/roles/:id',
        '/api/roles/:id/clone',
    ),
    'root': (),
    'scap_contents': (
        '/api/compliance/scap_contents',
        '/api/compliance/scap_contents',
        '/api/compliance/scap_contents/:id',
        '/api/compliance/scap_contents/:id',
        '/api/compliance/scap_contents/:id',
        '/api/compliance/scap_contents/:id/xml',
    ),
    'settings': ('/api/settings', '/api/settings/:id', '/api/settings/:id'),
    'smart_class_parameters': (
        '/api/smart_class_parameters',
        '/api/smart_class_parameters/:id',
        '/api/smart_class_parameters/:id',
    ),
    'smart_proxies': (
        '/api/smart_proxies',
        '/api/smart_proxies',
        '/api/smart_proxies/:id',
        '/api/smart_proxies/:id',
        '/api/smart_proxies/:id',
        '/api/smart_proxies/:id/import_puppetclasses',
        '/api/smart_proxies/:id/refresh',
    ),
    'smart_variables': (
        '/api/smart_variables',
        '/api/smart_variables',
        '/api/smart_variables/:id',
        '/api/smart_variables/:id',
        '/api/smart_variables/:id',
    ),
    'srpms': ('/katello/api/srpms/:id', '/katello/api/srpms/compare'),
    'ssh_keys': (
        '/api/users/:user_id/ssh_keys',
        '/api/users/:user_id/ssh_keys',
        '/api/users/:user_id/ssh_keys/:id',
        '/api/users/:user_id/ssh_keys/:id',
    ),
    'statistics': ('/api/statistics',),
    'subnet_disks': ('/bootdisk/api', '/bootdisk/api/subnets/:subnet_id'),
    'subnets': (
        '/api/subnets',
        '/api/subnets',
        '/api/subnets/:id',
        '/api/subnets/:id',
        '/api/subnets/:id',
        '/api/subnets/:id/freeip',
    ),
    'subscriptions': (
        '/katello/api/activation_keys/:activation_key_id/subscriptions',
        '/katello/api/organizations/:organization_id/subscriptions',
        '/katello/api/organizations/:organization_id/subscriptions/delete_manifest',
        '/katello/api/organizations/:organization_id/subscriptions/:id',
        '/katello/api/organizations/:organization_id/subscriptions/manifest_history',
        '/katello/api/organizations/:organization_id/subscriptions/refresh_manifest',
        '/katello/api/organizations/:organization_id/subscriptions/upload',
    ),
    'sync_plans': (
        '/katello/api/organizations/:organization_id/sync_plans',
        '/katello/api/organizations/:organization_id/sync_plans/:id',
        '/katello/api/organizations/:organization_id/sync_plans/:id',
        '/katello/api/organizations/:organization_id/sync_plans/:id',
        '/katello/api/organizations/:organization_id/sync_plans/:id/add_products',
        '/katello/api/organizations/:organization_id/sync_plans/:id/remove_products',
        '/katello/api/sync_plans',
        '/katello/api/sync_plans/:id/sync',
    ),
    'sync': ('/katello/api/organizations/:organization_id/products/:product_id/sync',),
    'tailoring_files': (
        '/api/compliance/tailoring_files',
        '/api/compliance/tailoring_files',
        '/api/compliance/tailoring_files/:id',
        '/api/compliance/tailoring_files/:id',
        '/api/compliance/tailoring_files/:id',
        '/api/compliance/tailoring_files/:id/xml',
    ),
    'tasks': ('/api/orchestration/:id/tasks',),
    'table_preferences': (
        '/api/users/:user_id/table_preferences/:name',
        '/api/users/:user_id/table_preferences/:name',
        '/api/users/:user_id/table_preferences',
        '/api/users/:user_id/table_preferences',
        '/api/users/:user_id/table_preferences/:name',
    ),
    'template': ('/api/templates/export', '/api/templates/import'),
    'template_combinations': (
        '/api/provisioning_templates/:provisioning_template_id/template_combinations/:id',
        '/api/template_combinations/:id',
        '/api/template_combinations/:id',
    ),
    'template_inputs': (
        '/api/templates/:template_id/template_inputs',
        '/api/templates/:template_id/template_inputs',
        '/api/templates/:template_id/template_inputs/:id',
        '/api/templates/:template_id/template_inputs/:id',
        '/api/templates/:template_id/template_inputs/:id',
    ),
    'template_invocations': ('/api/job_invocations/:job_invocation_id/template_invocations',),
    'template_kinds': ('/api/template_kinds',),
    'trends': ('/api/trends', '/api/trends/:id', '/api/trends', '/api/trends/:id'),
    'upstream_subscriptions': (
        '/katello/api/organizations/:organization_id/upstream_subscriptions',
        '/katello/api/organizations/:organization_id/upstream_subscriptions',
        '/katello/api/organizations/:organization_id/upstream_subscriptions',
        '/katello/api/organizations/:organization_id/upstream_subscriptions',
    ),
    'usergroups': (
        '/api/usergroups',
        '/api/usergroups',
        '/api/usergroups/:id',
        '/api/usergroups/:id',
        '/api/usergroups/:id',
    ),
    'users': (
        '/api/users',
        '/api/users/:id',
        '/api/current_user',
        '/api/users',
        '/api/users/:id',
        '/api/users/:id',
    ),
}


class AvailableURLsTestCase(TestCase):
    """Tests for ``api/v2``."""

    longMessage = True
    maxDiff = None

    def setUp(self):
        """Define commonly-used variables."""
        self.path = '{0}/api/v2'.format(settings.server.get_url())

    @tier1
    @upgrade
    def test_positive_get_status_code(self):
        """GET ``api/v2`` and examine the response.

        :id: 9d9c1afd-9158-419e-9a6e-91e9888f0c04

        :expectedresults: HTTP 200 is returned with an ``application/json``
            content-type

        """
        response = client.get(self.path, auth=settings.server.get_credentials(), verify=False)
        self.assertEqual(response.status_code, http.client.OK)
        self.assertIn('application/json', response.headers['content-type'])

    @tier1
    @upgrade
    def test_positive_get_links(self):
        """GET ``api/v2`` and check the links returned.

        :id: 7b2dd77a-a821-485b-94db-b583f93c9a89

        :expectedresults: The paths returned are equal to ``API_PATHS``.

        """
        # Did the server give us any paths at all?
        response = client.get(self.path, auth=settings.server.get_credentials(), verify=False)
        response.raise_for_status()
        # See below for an explanation of this transformation.
        api_paths = response.json()['links']
        for group, path_pairs in api_paths.items():
            api_paths[group] = list(path_pairs.values())
        self.assertEqual(frozenset(api_paths.keys()), frozenset(API_PATHS.keys()))
        for group in api_paths.keys():
            self.assertItemsEqual(api_paths[group], API_PATHS[group], group)
        # noqa (line-too-long)
        # response.json()['links'] is a dict like this:
        #
        #     {'content_views': {
        #          '…': '/katello/api/content_views/:id',
        #          '…': '/katello/api/content_views/:id/available_puppet_modules',
        #          '…': '/katello/api/organizations/:organization_id/content_views',
        #          '…': '/katello/api/organizations/:organization_id/content_views',
        #     }, …}
        #
        # We don't care about prose descriptions. It doesn't matter if those
        # change. Transform it before running any assertions:
        #
        #     {'content_views': [
        #          '/katello/api/content_views/:id',
        #          '/katello/api/content_views/:id/available_puppet_modules',
        #          '/katello/api/organizations/:organization_id/content_views',
        #          '/katello/api/organizations/:organization_id/content_views',
        #     ], …}


class EndToEndTestCase(TestCase, ClientProvisioningMixin):
    """End-to-end tests using the ``API`` path."""

    @classmethod
    def setUpClass(cls):  # noqa
        super(EndToEndTestCase, cls).setUpClass()
        cls.fake_manifest_is_set = setting_is_set('fake_manifest')

    @tier1
    @upgrade
    def test_positive_find_default_org(self):
        """Check if 'Default Organization' is present

        :id: c6e45b36-d8b6-4507-8dcd-0645668496b9

        :expectedresults: 'Default Organization' is found

        """
        results = entities.Organization().search(
            query={'search': 'name="{0}"'.format(DEFAULT_ORG)}
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, DEFAULT_ORG)

    @tier1
    @upgrade
    def test_positive_find_default_loc(self):
        """Check if 'Default Location' is present

        :id: 1f40b3c6-488d-4037-a7ab-250a02bf919a

        :expectedresults: 'Default Location' is found

        """
        results = entities.Location().search(query={'search': 'name="{0}"'.format(DEFAULT_LOC)})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, DEFAULT_LOC)

    @tier1
    @upgrade
    def test_positive_find_admin_user(self):
        """Check if Admin User is present

        :id: 892fdfcd-18c0-42ef-988b-f13a04097f5c

        :expectedresults: Admin User is found and has Admin role

        """
        results = entities.User().search(query={'search': 'login=admin'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].login, 'admin')

    @tier1
    @upgrade
    def test_positive_ping(self):
        """Check if all services are running

        :id: b8ecc7ba-8007-4067-bf99-21a82c833de7

        :expectedresults: Overall and individual services status should be
            'ok'.

        """
        response = entities.Ping().search_json()
        self.assertEqual(response['status'], 'ok')  # overall status

        # Check that all services are OK. ['services'] is in this format:
        #
        # {'services': {
        #    'candlepin': {'duration_ms': '40', 'status': 'ok'},
        #    'candlepin_auth': {'duration_ms': '41', 'status': 'ok'},
        #    …
        # }, 'status': 'ok'}
        services = response['services']
        self.assertTrue(
            all([service['status'] == 'ok' for service in services.values()]),
            'Not all services seem to be up and running!',
        )

    @skip_if_not_set('compute_resources')
    @tier4
    @upgrade
    def test_positive_end_to_end(self):
        """Perform end to end smoke tests using RH and custom repos.

        1. Create a new user with admin permissions
        2. Using the new user from above
            1. Create a new organization
            2. Clone and upload manifest
            3. Create a new lifecycle environment
            4. Create a custom product
            5. Create a custom YUM repository
            6. Create a custom PUPPET repository
            7. Enable a Red Hat repository
            8. Synchronize the three repositories
            9. Create a new content view
            10. Associate the YUM and Red Hat repositories to new content view
            11. Add a PUPPET module to new content view
            12. Publish content view
            13. Promote content view to the lifecycle environment
            14. Create a new activation key
            15. Add the products to the activation key
            16. Create a new libvirt compute resource
            17. Create a new subnet
            18. Create a new domain
            19. Create a new hostgroup and associate previous entities to it
            20. Provision a client

        :id: b2f73740-d3ce-4e6e-abc7-b23e5562bac1

        :expectedresults: All tests should succeed and Content should be
            successfully fetched by client.
        """
        # step 1: Create a new user with admin permissions
        login = gen_string('alphanumeric')
        password = gen_string('alphanumeric')
        entities.User(admin=True, login=login, password=password).create()

        # step 2.1: Create a new organization
        server_config = get_nailgun_config()
        server_config.auth = (login, password)
        org = entities.Organization(server_config).create()

        # step 2.2: Clone and upload manifest
        if self.fake_manifest_is_set:
            with manifests.clone() as manifest:
                upload_manifest(org.id, manifest.content)

        # step 2.3: Create a new lifecycle environment
        le1 = entities.LifecycleEnvironment(server_config, organization=org).create()

        # step 2.4: Create a custom product
        prod = entities.Product(server_config, organization=org).create()
        repositories = []

        # step 2.5: Create custom YUM repository
        repo1 = entities.Repository(
            server_config, product=prod, content_type='yum', url=CUSTOM_RPM_REPO
        ).create()
        repositories.append(repo1)

        # step 2.6: Create custom PUPPET repository
        repo2 = entities.Repository(
            server_config, product=prod, content_type='puppet', url=FAKE_0_PUPPET_REPO
        ).create()
        repositories.append(repo2)

        # step 2.7: Enable a Red Hat repository
        if self.fake_manifest_is_set:
            repo3 = entities.Repository(
                id=enable_rhrepo_and_fetchid(
                    basearch='x86_64',
                    org_id=org.id,
                    product=PRDS['rhel'],
                    repo=REPOS['rhva6']['name'],
                    reposet=REPOSET['rhva6'],
                    releasever='6Server',
                )
            )
            repositories.append(repo3)

        # step 2.8: Synchronize the three repositories
        for repo in repositories:
            repo.sync()

        # step 2.9: Create content view
        content_view = entities.ContentView(server_config, organization=org).create()

        # step 2.10: Associate the YUM and Red Hat repositories to new content
        # view
        repositories.remove(repo2)
        content_view.repository = repositories
        content_view = content_view.update(['repository'])

        # step 2.11: Add a PUPPET module to new content view
        puppet_mods = content_view.available_puppet_modules()
        self.assertGreater(len(puppet_mods['results']), 0)
        puppet_module = random.choice(puppet_mods['results'])
        puppet = entities.ContentViewPuppetModule(
            author=puppet_module['author'], content_view=content_view, name=puppet_module['name']
        ).create()
        self.assertEqual(puppet.name, puppet_module['name'])

        # step 2.12: Publish content view
        content_view.publish()

        # step 2.13: Promote content view to the lifecycle environment
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        cv_version = content_view.version[0].read()
        self.assertEqual(len(cv_version.environment), 1)
        promote(cv_version, le1.id)
        # check that content view exists in lifecycle
        content_view = content_view.read()
        self.assertEqual(len(content_view.version), 1)
        cv_version = cv_version.read()

        # step 2.14: Create a new activation key
        activation_key_name = gen_string('alpha')
        activation_key = entities.ActivationKey(
            name=activation_key_name, environment=le1, organization=org, content_view=content_view
        ).create()

        # step 2.15: Add the products to the activation key
        for sub in entities.Subscription(organization=org).search():
            if sub.name == DEFAULT_SUBSCRIPTION_NAME:
                activation_key.add_subscriptions(data={'quantity': 1, 'subscription_id': sub.id})
                break
        # step 2.15.1: Enable product content
        if self.fake_manifest_is_set:
            activation_key.content_override(
                data={'content_overrides': [{'content_label': AK_CONTENT_LABEL, 'value': '1'}]}
            )

        # BONUS: Create a content host and associate it with promoted
        # content view and last lifecycle where it exists
        content_host = entities.Host(
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': le1.id,
            },
            organization=org,
        ).create()
        # check that content view matches what we passed
        self.assertEqual(content_host.content_facet_attributes['content_view_id'], content_view.id)
        # check that lifecycle environment matches
        self.assertEqual(content_host.content_facet_attributes['lifecycle_environment_id'], le1.id)

        # step 2.16: Create a new libvirt compute resource
        entities.LibvirtComputeResource(
            server_config,
            url='qemu+ssh://root@{0}/system'.format(settings.compute_resources.libvirt_hostname),
        ).create()

        # step 2.17: Create a new subnet
        subnet = entities.Subnet(server_config).create()

        # step 2.18: Create a new domain
        domain = entities.Domain(server_config).create()

        # step 2.19: Create a new hostgroup and associate previous entities to
        # it
        entities.HostGroup(server_config, domain=domain, subnet=subnet).create()

        # step 2.20: Provision a client
        self.client_provisioning(activation_key_name, org.label)
