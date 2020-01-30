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
import random
import pytest

from fauxfactory import gen_string
from nailgun import client, entities
from robottelo import manifests
from robottelo.api.utils import (
    enable_rhrepo_and_fetchid,
    promote,
    upload_manifest,
)
from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_LOC,
    DEFAULT_ORG,
    DEFAULT_SUBSCRIPTION_NAME,
    FAKE_0_PUPPET_REPO,
    CUSTOM_RPM_REPO,
    PRDS,
    REPOS,
    REPOSET,
)
from robottelo.decorators import (
    setting_is_set,
    skip_if_not_set,
    tier1,
    tier4,
    upgrade
)
from robottelo.helpers import get_nailgun_config
from robottelo.test import TestCase
from six.moves import http_client
from .utils import AK_CONTENT_LABEL, ClientProvisioningMixin
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
    u'ansible_collections': (
        u'/katello/api/ansible_collections/compare',
        u'/katello/api/ansible_collections/:id',
    ),
    u'ansible_inventories': (
        u'/api/ansible_inventories/hosts',
        u'/api/ansible_inventories/schedule',
    ),
    u'ansible_override_values': (
        u'/ansible/api/ansible_override_values',
        u'/ansible/api/ansible_override_values/:id',
    ),
    u'ansible_roles': (
        u'/ansible/api/ansible_roles',
        u'/ansible/api/ansible_roles/:id',
        u'/ansible/api/ansible_roles/:id',
        u'/ansible/api/ansible_roles/fetch',
        u'/ansible/api/ansible_roles/import',
        u'/ansible/api/ansible_roles/obsolete',
    ),
    u'ansible_variables': (
        u'/ansible/api/ansible_variables/:id',
        u'/ansible/api/ansible_variables',
        u'/ansible/api/ansible_variables/:id',
        u'/ansible/api/ansible_variables',
        u'/ansible/api/ansible_variables/:id',
        u'/ansible/api/ansible_variables/import',
        u'/ansible/api/ansible_variables/obsolete',
    ),
    u'api': (),
    u'architectures': (
        u'/api/architectures',
        u'/api/architectures',
        u'/api/architectures/:id',
        u'/api/architectures/:id',
        u'/api/architectures/:id',
    ),
    u'arf_reports': (
        u'/api/compliance/arf/:cname/:policy_id/:date',
        u'/api/compliance/arf_reports',
        u'/api/compliance/arf_reports/:id',
        u'/api/compliance/arf_reports/:id',
        u'/api/compliance/arf_reports/:id/download',
        u'/api/compliance/arf_reports/:id/download_html',
    ),
    u'audits': (
        u'/api/audits',
        u'/api/audits/:id',
    ),
    u'auth_source_externals': (
        u'/api/auth_source_externals',
        u'/api/auth_source_externals/:id',
        u'/api/auth_source_externals/:id',
    ),
    u'auth_source_internals': (
        u'/api/auth_source_internals',
        u'/api/auth_source_internals/:id',
    ),
    u'auth_source_ldaps': (
        u'/api/auth_source_ldaps',
        u'/api/auth_source_ldaps',
        u'/api/auth_source_ldaps/:id',
        u'/api/auth_source_ldaps/:id',
        u'/api/auth_source_ldaps/:id',
        u'/api/auth_source_ldaps/:id/test',
    ),
    u'auth_sources': (
        u'/api/auth_sources',
    ),
    u'autosign': (
        u'/api/smart_proxies/:smart_proxy_id/autosign',
        u'/api/smart_proxies/:smart_proxy_id/autosign',
        u'/api/smart_proxies/:smart_proxy_id/autosign/:id',
    ),
    u'base': (),
    u'bookmarks': (
        u'/api/bookmarks',
        u'/api/bookmarks',
        u'/api/bookmarks/:id',
        u'/api/bookmarks/:id',
        u'/api/bookmarks/:id',
    ),
    u'candlepin_dynflow_proxy': (
        u'/katello/api/consumers/:id/profiles',
        u'/katello/api/systems/:id/deb_package_profile',
    ),
    u'candlepin_proxies': (
        u'/katello/api/consumers/:id/tracer',
        u'/katello/api/systems/:id/enabled_repos',
    ),
    u'capsule_content': (
        u'/katello/api/capsules/:id/content/available_lifecycle_environments',
        u'/katello/api/capsules/:id/content/lifecycle_environments',
        u'/katello/api/capsules/:id/content/lifecycle_environments',
        u'/katello/api/capsules/:id/content/lifecycle_environments/:environment_id',
        u'/katello/api/capsules/:id/content/sync',
        u'/katello/api/capsules/:id/content/sync',
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
        u'/api/compute_resources/:compute_resource_id/compute_profiles/:compute_profile_id/compute_attributes',
        u'/api/compute_resources/:compute_resource_id/compute_profiles/:compute_profile_id/compute_attributes/:id'
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
        u'/api/compute_resources/:id/available_flavors',
        u'/api/compute_resources/:id/available_folders',
        u'/api/compute_resources/:id/available_images',
        u'/api/compute_resources/:id/available_networks',
        u'/api/compute_resources/:id/available_security_groups',
        u'/api/compute_resources/:id/available_storage_domains',
        u'/api/compute_resources/:id/available_storage_pods',
        u'/api/compute_resources/:id/available_zones',
        u'/api/compute_resources/:id/refresh_cache',
        u'/api/compute_resources/:id/storage_domains/:storage_domain_id',
        u'/api/compute_resources/:id/storage_pods/:storage_pod_id'
    ),
    u'configs': (
        u'/foreman_virt_who_configure/api/v2/configs',
        u'/foreman_virt_who_configure/api/v2/configs',
        u'/foreman_virt_who_configure/api/v2/configs/:id',
        u'/foreman_virt_who_configure/api/v2/configs/:id',
        u'/foreman_virt_who_configure/api/v2/configs/:id',
        u'/foreman_virt_who_configure/api/v2/configs/:id/deploy_script',
    ),
    u'config_groups': (
        u'/api/config_groups',
        u'/api/config_groups',
        u'/api/config_groups/:id',
        u'/api/config_groups/:id',
        u'/api/config_groups/:id',
    ),
    u'config_reports': (
        u'/api/config_reports',
        u'/api/config_reports',
        u'/api/config_reports/:id',
        u'/api/config_reports/:id',
        u'/api/hosts/:host_id/config_reports/last',

    ),
    u'config_templates': (
        u'/api/config_templates',
        u'/api/config_templates',
        u'/api/config_templates/:id',
        u'/api/config_templates/:id',
        u'/api/config_templates/:id',
        u'/api/config_templates/:id/clone',
        u'/api/config_templates/build_pxe_default',
    ),
    u'content_credentials': (
        u'/katello/api/content_credentials',
        u'/katello/api/content_credentials',
        u'/katello/api/content_credentials/:id',
        u'/katello/api/content_credentials/:id',
        u'/katello/api/content_credentials/:id',
        u'/katello/api/content_credentials/:id/content',
        u'/katello/api/content_credentials/:id/content',
    ),
    u'content_uploads': (
        u'/katello/api/repositories/:repository_id/content_uploads',
        u'/katello/api/repositories/:repository_id/content_uploads/:id',
        u'/katello/api/repositories/:repository_id/content_uploads/:id',
    ),
    u'content_view_components': (
        u'/katello/api/content_views/:composite_content_view_id/content_view_components',
        u'/katello/api/content_views/:composite_content_view_id/content_view_components/:id',
        u'/katello/api/content_views/:composite_content_view_id/content_view_components/:id',
        u'/katello/api/content_views/:composite_content_view_id/content_view_components/add',
        u'/katello/api/content_views/:composite_content_view_id/content_view_components/remove',
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
        u'/katello/api/content_views/:id/publish',
        u'/katello/api/content_views/:id/remove',
        u'/katello/api/organizations/:organization_id/content_views',
        u'/katello/api/organizations/:organization_id/content_views',
    ),
    u'content_view_histories': (
        u'/katello/api/content_views/:id/history',
    ),
    u'content_view_versions': (
        u'/katello/api/content_view_versions',
        u'/katello/api/content_view_versions/:id',
        u'/katello/api/content_view_versions/:id',
        u'/katello/api/content_view_versions/:id',
        u'/katello/api/content_view_versions/:id/export',
        u'/katello/api/content_view_versions/:id/promote',
        u'/katello/api/content_view_versions/:id/republish_repositories',
        u'/katello/api/content_view_versions/incremental_update',
    ),
    u'dashboard': (
        u'/api/dashboard',
    ),
    u'debs': (
        u'/katello/api/debs/:id',
        u'/katello/api/debs/compare',
    ),
    u'discovered_hosts': (
        u'/api/v2/discovered_hosts',
        u'/api/v2/discovered_hosts',
        u'/api/v2/discovered_hosts/:id',
        u'/api/v2/discovered_hosts/:id',
        u'/api/v2/discovered_hosts/:id',
        u'/api/v2/discovered_hosts/:id/auto_provision',
        u'/api/v2/discovered_hosts/:id/reboot',
        u'/api/v2/discovered_hosts/:id/refresh_facts',
        u'/api/v2/discovered_hosts/auto_provision_all',
        u'/api/v2/discovered_hosts/facts',
        u'/api/v2/discovered_hosts/reboot_all',
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
    u'docker_manifests': (
        u'/katello/api/docker_manifests/:id',
        u'/katello/api/docker_manifests/compare',
    ),
    u'docker_manifest_lists': (
        u'/katello/api/docker_manifest_lists/:id',
        u'/katello/api/docker_manifest_lists/compare',
    ),
    u'docker_tags': (
        u'/katello/api/docker_tags/compare',
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
        u'/katello/api/content_view_versions/:id/available_errata',
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
    u'file_units': (
        u'/katello/api/files/compare',
        u'/katello/api/files/:id',
    ),
    u'filters': (
        u'/api/filters',
        u'/api/filters',
        u'/api/filters/:id',
        u'/api/filters/:id',
        u'/api/filters/:id',
    ),
    u'foreign_input_sets': (
        '/api/templates/:template_id/foreign_input_sets',
        '/api/templates/:template_id/foreign_input_sets',
        '/api/templates/:template_id/foreign_input_sets/:id',
        '/api/templates/:template_id/foreign_input_sets/:id',
        '/api/templates/:template_id/foreign_input_sets/:id',
    ),
    u'foreman_tasks': (
        u'/foreman_tasks/api/tasks',
        u'/foreman_tasks/api/tasks/:id',
        u'/foreman_tasks/api/tasks/:id/details',
        u'/foreman_tasks/api/tasks/:id/sub_tasks',
        u'/foreman_tasks/api/tasks/bulk_resume',
        u'/foreman_tasks/api/tasks/bulk_search',
        u'/foreman_tasks/api/tasks/callback',
        u'/foreman_tasks/api/tasks/summary',
    ),
    u'gpg_keys': (
        u'/katello/api/gpg_keys',
        u'/katello/api/gpg_keys',
        u'/katello/api/gpg_keys/:id',
        u'/katello/api/gpg_keys/:id',
        u'/katello/api/gpg_keys/:id',
        u'/katello/api/gpg_keys/:id/content',
        u'/katello/api/gpg_keys/:id/content',
    ),
    u'home': (
        u'/api',
        u'/api/status',
    ),
    u'host_autocomplete': (),
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
        u'/katello/api/host_collections/:id/add_hosts',
        u'/katello/api/host_collections/:id/copy',
        u'/katello/api/host_collections/:id/remove_hosts',
    ),
    u'host_debs': (
        u'/api/hosts/:host_id/debs',
    ),
    u'host_module_streams': (
        u'/api/hosts/:host_id/module_streams',
    ),
    u'host_subscriptions': (
        u'/api/hosts/:host_id/subscriptions',
        u'/api/hosts/:host_id/subscriptions',
        u'/api/hosts/:host_id/subscriptions/add_subscriptions',
        u'/api/hosts/:host_id/subscriptions/auto_attach',
        u'/api/hosts/:host_id/subscriptions/available_release_versions',
        u'/api/hosts/:host_id/subscriptions/content_override',
        u'/api/hosts/:host_id/subscriptions/events',
        u'/api/hosts/:host_id/subscriptions/product_content',
        u'/api/hosts/subscriptions',
    ),
    u'host_tracer': (
        u'/api/hosts/:host_id/traces',
    ),
    u'hostgroup_classes': (
        u'/api/hostgroups/:hostgroup_id/puppetclass_ids',
        u'/api/hostgroups/:hostgroup_id/puppetclass_ids',
        u'/api/hostgroups/:hostgroup_id/puppetclass_ids/:id',
    ),
    u'hostgroups': (
        u'/api/hostgroups',
        u'/api/hostgroups/:id',
        u'/api/hostgroups',
        u'/api/hostgroups/:id',
        u'/api/hostgroups/:id',
        u'/api/hostgroups/:id/clone',
        u'/api/hostgroups/:id/rebuild_config',
        u'/api/hostgroups/:id/play_roles',
        u'/api/hostgroups/multiple_play_roles',
        u'/api/hostgroups/:id/ansible_roles',
        u'/api/hostgroups/:id/assign_ansible_roles'
    ),
    u'hosts': (
        u'/api/hosts',
        u'/api/hosts/:id',
        u'/api/hosts',
        u'/api/hosts/:id',
        u'/api/hosts/:id',
        u'/api/hosts/:id/enc',
        u'/api/hosts/:id/status',
        u'/api/hosts/:id/status/:type',
        u'/api/hosts/:id/vm_compute_attributes',
        u'/api/hosts/:id/disassociate',
        u'/api/hosts/:id/power',
        u'/api/hosts/:id/power',
        u'/api/hosts/:id/boot',
        u'/api/hosts/facts',
        u'/api/hosts/:id/rebuild_config',
        u'/api/hosts/:id/template/:kind',
        u'/api/hosts/:id/play_roles',
        u'/api/hosts/multiple_play_roles',
        u'/api/hosts/:id/ansible_roles',
        u'/api/hosts/:id/assign_ansible_roles',
        u'/api/hosts/:host_id/host_collections',
        u'/api/hosts/:id/policies_enc'
    ),
    u'hosts_bulk_actions': (
        u'/api/hosts/bulk/add_host_collections',
        u'/api/hosts/bulk/add_subscriptions',
        u'/api/hosts/bulk/auto_attach',
        u'/api/hosts/bulk/applicable_errata',
        u'/api/hosts/bulk/available_incremental_updates',
        u'/api/hosts/bulk/content_overrides',
        u'/api/hosts/bulk/destroy',
        u'/api/hosts/bulk/environment_content_view',
        u'/api/hosts/bulk/install_content',
        u'/api/hosts/bulk/installable_errata',
        u'/api/hosts/bulk/module_streams',
        u'/api/hosts/bulk/release_version',
        u'/api/hosts/bulk/remove_content',
        u'/api/hosts/bulk/remove_host_collections',
        u'/api/hosts/bulk/remove_subscriptions',
        u'/api/hosts/bulk/update_content',
    ),
    u'host_errata': (
        u'/api/hosts/:host_id/errata',
        u'/api/hosts/:host_id/errata/:id',
        u'/api/hosts/:host_id/errata/applicability',
        u'/api/hosts/:host_id/errata/apply',
    ),
    u'host_packages': (
        u'/api/hosts/:host_id/packages',
        u'/api/hosts/:host_id/packages/install',
        u'/api/hosts/:host_id/packages/remove',
        u'/api/hosts/:host_id/packages/upgrade_all',
    ),
    u'http_proxies': (
        u'/api/http_proxies',
        u'/api/http_proxies',
        u'/api/http_proxies/:id',
        u'/api/http_proxies/:id',
        u'/api/http_proxies/:id',
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
    u'job_invocations': (
        u'/api/job_invocations',
        u'/api/job_invocations',
        u'/api/job_invocations/:id',
        u'/api/job_invocations/:id/cancel',
        u'/api/job_invocations/:id/hosts/:host_id',
        u'/api/job_invocations/:id/hosts/:host_id/raw',
        u'/api/job_invocations/:id/rerun',
    ),
    u'job_templates': (
        u'/api/job_templates',
        u'/api/job_templates',
        u'/api/job_templates/:id',
        u'/api/job_templates/:id',
        u'/api/job_templates/:id',
        u'/api/job_templates/:id/clone',
        u'/api/job_templates/:id/export',
        u'/api/job_templates/import',
    ),
    u'lifecycle_environments': (
        u'/katello/api/environments',
        u'/katello/api/environments',
        u'/katello/api/environments/:id',
        u'/katello/api/environments/:id',
        u'/katello/api/environments/:id',
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
    u'module_streams': (
        u'/katello/api/module_streams/compare',
        u'/katello/api/module_streams/:id'
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
        u'/katello/api/organizations/:id/releases',
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
    u'ostree_branches': (
        u'/katello/api/ostree_branches/:id',
        u'/katello/api/ostree_branches/compare',
    ),
    u'override_values': (
        u'/api/smart_variables/:smart_variable_id/override_values',
        u'/api/smart_variables/:smart_variable_id/override_values',
        u'/api/smart_variables/:smart_variable_id/override_values/:id',
        u'/api/smart_variables/:smart_variable_id/override_values/:id',
        u'/api/smart_variables/:smart_variable_id/override_values/:id',
    ),
    u'package_groups': (
        u'/katello/api/package_group',
        u'/katello/api/package_group',
        u'/katello/api/package_groups/:id',
        u'/katello/api/package_groups/compare',
    ),
    u'packages': (
        u'/katello/api/packages/:id',
        u'/katello/api/packages/compare'
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
    u'personal_access_tokens': (
        u'/api/users/:user_id/personal_access_tokens',
        u'/api/users/:user_id/personal_access_tokens',
        u'/api/users/:user_id/personal_access_tokens/:id',
        u'/api/users/:user_id/personal_access_tokens/:id',
    ),
    u'ping': (
        u'/katello/api/ping',
        u'/katello/api/status',
        u'/api/ping',
        u'/api/statuses',
    ),
    u'plugins': (
        u'/api/plugins',
    ),
    u'policies': (
        u'/api/compliance/policies',
        u'/api/compliance/policies',
        u'/api/compliance/policies/:id',
        u'/api/compliance/policies/:id',
        u'/api/compliance/policies/:id',
        u'/api/compliance/policies/:id/content',
        u'/api/compliance/policies/:id/tailoring',
    ),
    u'products_bulk_actions': (
        u'/katello/api/products/bulk/destroy',
        u'/katello/api/products/bulk/http_proxy',
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
    u'provisioning_templates': (
        u'/api/provisioning_templates',
        u'/api/provisioning_templates',
        u'/api/provisioning_templates/:id',
        u'/api/provisioning_templates/:id',
        u'/api/provisioning_templates/:id',
        u'/api/provisioning_templates/:id/clone',
        u'/api/provisioning_templates/:id/export',
        u'/api/provisioning_templates/build_pxe_default',
        u'/api/provisioning_templates/import',
    ),
    u'ptables': (
        u'/api/ptables',
        u'/api/ptables',
        u'/api/ptables/:id',
        u'/api/ptables/:id',
        u'/api/ptables/:id',
        u'/api/ptables/:id/clone',
        u'/api/ptables/:id/export',
        u'/api/ptables/import',
    ),
    u'puppetclasses': (
        u'/api/puppetclasses',
        u'/api/puppetclasses',
        u'/api/puppetclasses/:id',
        u'/api/puppetclasses/:id',
        u'/api/puppetclasses/:id',
    ),
    u'puppet_hosts': (
        u'/api/hosts/:id/puppetrun',
    ),
    u'puppet_modules': (
        u'/katello/api/puppet_modules/compare',
        u'/katello/api/puppet_modules/:id',
    ),
    u'realms': (
        u'/api/realms',
        u'/api/realms',
        u'/api/realms/:id',
        u'/api/realms/:id',
        u'/api/realms/:id',
    ),
    u'recurring_logics': (
        u'/foreman_tasks/api/recurring_logics',
        u'/foreman_tasks/api/recurring_logics/:id',
        u'/foreman_tasks/api/recurring_logics/:id',
        u'/foreman_tasks/api/recurring_logics/:id/cancel'
    ),
    u'remote_execution_features': (
        '/api/remote_execution_features',
        '/api/remote_execution_features/:id',
        '/api/remote_execution_features/:id',
    ),
    u'reports': (
        u'/api/hosts/:host_id/reports/last',
        u'/api/reports',
        u'/api/reports',
        u'/api/reports/:id',
        u'/api/reports/:id',
    ),
    u'report_templates': (
        u'/api/report_templates',
        u'/api/report_templates/:id',
        u'/api/report_templates',
        u'/api/report_templates/import',
        u'/api/report_templates/:id',
        u'/api/report_templates/:id',
        u'/api/report_templates/:id/clone',
        u'/api/report_templates/:id/export',
        u'/api/report_templates/:id/generate',
        u'/api/report_templates/:id/schedule_report',
        u'/api/report_templates/:id/report_data/:job_id',
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
        u'/katello/api/repositories/:id/export',
        u'/katello/api/repositories/:id/gpg_key_content',
        u'/katello/api/repositories/:id/import_uploads',
        u'/katello/api/repositories/:id/republish',
        u'/katello/api/repositories/:id/sync',
        u'/katello/api/repositories/:id/upload_content',
        u'/katello/api/repositories/repository_types',
    ),
    u'repository_sets': (
        u'/katello/api/repository_sets',
        u'/katello/api/repository_sets/:id',
        u'/katello/api/repository_sets/:id/available_repositories',
        u'/katello/api/repository_sets/:id/disable',
        u'/katello/api/repository_sets/:id/enable',
    ),
    u'roles': (
        u'/api/roles',
        u'/api/roles',
        u'/api/roles/:id',
        u'/api/roles/:id',
        u'/api/roles/:id',
        u'/api/roles/:id/clone',
    ),
    u'root': (),
    u'scap_contents': (
        u'/api/compliance/scap_contents',
        u'/api/compliance/scap_contents',
        u'/api/compliance/scap_contents/:id',
        u'/api/compliance/scap_contents/:id',
        u'/api/compliance/scap_contents/:id',
        u'/api/compliance/scap_contents/:id/xml',
    ),
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
    u'srpms': (
        u'/katello/api/srpms/:id',
        u'/katello/api/srpms/compare',
    ),
    u'ssh_keys': (
        u'/api/users/:user_id/ssh_keys',
        u'/api/users/:user_id/ssh_keys',
        u'/api/users/:user_id/ssh_keys/:id',
        u'/api/users/:user_id/ssh_keys/:id',
    ),
    u'statistics': (
        u'/api/statistics',
    ),
    u'subnet_disks': (
        u'/bootdisk/api',
        u'/bootdisk/api/subnets/:subnet_id',
    ),
    u'subnets': (
        u'/api/subnets',
        u'/api/subnets',
        u'/api/subnets/:id',
        u'/api/subnets/:id',
        u'/api/subnets/:id',
        u'/api/subnets/:id/freeip',
    ),
    u'subscriptions': (
        u'/katello/api/activation_keys/:activation_key_id/subscriptions',
        u'/katello/api/organizations/:organization_id/subscriptions',
        u'/katello/api/organizations/:organization_id/subscriptions/delete_manifest',
        u'/katello/api/organizations/:organization_id/subscriptions/:id',
        u'/katello/api/organizations/:organization_id/subscriptions/manifest_history',
        u'/katello/api/organizations/:organization_id/subscriptions/refresh_manifest',
        u'/katello/api/organizations/:organization_id/subscriptions/upload',
    ),
    u'sync_plans': (
        u'/katello/api/organizations/:organization_id/sync_plans',
        u'/katello/api/organizations/:organization_id/sync_plans/:id',
        u'/katello/api/organizations/:organization_id/sync_plans/:id',
        u'/katello/api/organizations/:organization_id/sync_plans/:id',
        u'/katello/api/organizations/:organization_id/sync_plans/:id/add_products',
        u'/katello/api/organizations/:organization_id/sync_plans/:id/remove_products',
        u'/katello/api/sync_plans',
        u'/katello/api/sync_plans/:id/sync',
    ),
    u'sync': (
        u'/katello/api/organizations/:organization_id/products/:product_id/sync',
    ),
    u'tailoring_files': (
        u'/api/compliance/tailoring_files',
        u'/api/compliance/tailoring_files',
        u'/api/compliance/tailoring_files/:id',
        u'/api/compliance/tailoring_files/:id',
        u'/api/compliance/tailoring_files/:id',
        u'/api/compliance/tailoring_files/:id/xml',
    ),
    u'tasks': (
        u'/api/orchestration/:id/tasks',
    ),
    u'table_preferences': (
        u'/api/users/:user_id/table_preferences/:name',
        u'/api/users/:user_id/table_preferences/:name',
        u'/api/users/:user_id/table_preferences',
        u'/api/users/:user_id/table_preferences',
        u'/api/users/:user_id/table_preferences/:name',
    ),
    u'template': (
        u'/api/templates/export',
        u'/api/templates/import',
    ),
    u'template_combinations': (
        u'/api/config_templates/:config_template_id/template_combinations',
        u'/api/config_templates/:config_template_id/template_combinations',
        u'/api/provisioning_templates/:provisioning_template_id/template_combinations/:id',
        u'/api/template_combinations/:id',
        u'/api/template_combinations/:id',
    ),
    u'template_inputs': (
        '/api/templates/:template_id/template_inputs',
        '/api/templates/:template_id/template_inputs',
        '/api/templates/:template_id/template_inputs/:id',
        '/api/templates/:template_id/template_inputs/:id',
        '/api/templates/:template_id/template_inputs/:id',
    ),
    u'template_invocations': (
        u'/api/job_invocations/:job_invocation_id/template_invocations',
    ),
    u'template_kinds': (
        u'/api/template_kinds',
    ),
    u'trends': (
        u'/api/trends',
        u'/api/trends/:id',
        u'/api/trends',
        u'/api/trends/:id',
    ),
    u'upstream_subscriptions': (
        u'/katello/api/organizations/:organization_id/upstream_subscriptions',
        u'/katello/api/organizations/:organization_id/upstream_subscriptions',
        u'/katello/api/organizations/:organization_id/upstream_subscriptions',
        u'/katello/api/organizations/:organization_id/upstream_subscriptions',
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
        u'/api/users/:id',
        u'/api/current_user',
        u'/api/users',
        u'/api/users/:id',
        u'/api/users/:id'
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
        response = client.get(
            self.path,
            auth=settings.server.get_credentials(),
            verify=False,
        )
        self.assertEqual(response.status_code, http_client.OK)
        self.assertIn('application/json', response.headers['content-type'])

    @tier1
    @upgrade
    def test_positive_get_links(self):
        """GET ``api/v2`` and check the links returned.

        :id: 7b2dd77a-a821-485b-94db-b583f93c9a89

        :expectedresults: The paths returned are equal to ``API_PATHS``.

        """
        # Did the server give us any paths at all?
        response = client.get(
            self.path,
            auth=settings.server.get_credentials(),
            verify=False,
        )
        response.raise_for_status()
        # See below for an explanation of this transformation.
        api_paths = response.json()['links']
        for group, path_pairs in api_paths.items():
            api_paths[group] = list(path_pairs.values())
        self.assertEqual(
            frozenset(api_paths.keys()),
            frozenset(API_PATHS.keys())
        )
        for group in api_paths.keys():
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
        results = entities.Location().search(
            query={'search': 'name="{0}"'.format(DEFAULT_LOC)}
        )
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
        self.assertEqual(response['status'], u'ok')  # overall status

        # Check that all services are OK. ['services'] is in this format:
        #
        # {u'services': {
        #    u'candlepin': {u'duration_ms': u'40', u'status': u'ok'},
        #    u'candlepin_auth': {u'duration_ms': u'41', u'status': u'ok'},
        #    …
        # }, u'status': u'ok'}
        services = response['services']
        self.assertTrue(
            all([service['status'] == u'ok' for service in services.values()]),
            u'Not all services seem to be up and running!'
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
        le1 = entities.LifecycleEnvironment(
            server_config,
            organization=org
        ).create()

        # step 2.4: Create a custom product
        prod = entities.Product(server_config, organization=org).create()
        repositories = []


        # step 2.5: Create custom YUM repository
        repo1 = entities.Repository(
            server_config,
            product=prod,
            content_type=u'yum',
            url=CUSTOM_RPM_REPO
        ).create()
        repositories.append(repo1)

        # step 2.6: Create custom PUPPET repository
        repo2 = entities.Repository(
            server_config,
            product=prod,
            content_type=u'puppet',
            url=FAKE_0_PUPPET_REPO
        ).create()
        repositories.append(repo2)

        # step 2.7: Enable a Red Hat repository
        if self.fake_manifest_is_set:
            repo3 = entities.Repository(id=enable_rhrepo_and_fetchid(
                basearch='x86_64',
                org_id=org.id,
                product=PRDS['rhel'],
                repo=REPOS['rhva6']['name'],
                reposet=REPOSET['rhva6'],
                releasever='6Server',
            ))
            repositories.append(repo3)

        # step 2.8: Synchronize the three repositories
        for repo in repositories:
            repo.sync()

        # step 2.9: Create content view
        content_view = entities.ContentView(
            server_config,
            organization=org
        ).create()

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
            author=puppet_module['author'],
            content_view=content_view,
            name=puppet_module['name'],
        ).create()
        self.assertEqual(
            puppet.name,
            puppet_module['name'],
        )

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
            name=activation_key_name,
            environment=le1,
            organization=org,
            content_view=content_view,
        ).create()

        # step 2.15: Add the products to the activation key
        for sub in entities.Subscription(organization=org).search():
            if sub.name == DEFAULT_SUBSCRIPTION_NAME:
                activation_key.add_subscriptions(data={
                    'quantity': 1,
                    'subscription_id': sub.id,
                })
                break
        # step 2.15.1: Enable product content
        if self.fake_manifest_is_set:
            activation_key.content_override(data={'content_override': {
                u'content_label': AK_CONTENT_LABEL,
                u'value': u'1',
            }})

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
        self.assertEqual(
            content_host.content_facet_attributes['content_view_id'],
            content_view.id
        )
        # check that lifecycle environment matches
        self.assertEqual(
            content_host.content_facet_attributes['lifecycle_environment_id'],
            le1.id
        )

        # step 2.16: Create a new libvirt compute resource
        entities.LibvirtComputeResource(
            server_config,
            url=u'qemu+ssh://root@{0}/system'.format(
                settings.compute_resources.libvirt_hostname
            ),
        ).create()

        # step 2.17: Create a new subnet
        subnet = entities.Subnet(server_config).create()

        # step 2.18: Create a new domain
        domain = entities.Domain(server_config).create()

        # step 2.19: Create a new hostgroup and associate previous entities to
        # it
        entities.HostGroup(
            server_config,
            domain=domain,
            subnet=subnet
        ).create()

        # step 2.20: Provision a client
        self.client_provisioning(activation_key_name, org.label)
