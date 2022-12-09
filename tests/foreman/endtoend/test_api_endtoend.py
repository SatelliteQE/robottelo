"""Smoke tests for the ``API`` end-to-end scenario.

:Requirement: Api Endtoend

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:Assignee: gtalreja

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import http
import random
from collections import defaultdict
from pprint import pformat

import pytest
from deepdiff import DeepDiff
from fauxfactory import gen_string
from nailgun import client
from nailgun import entities

from robottelo import constants
from robottelo.api.utils import enable_rhrepo_and_fetchid
from robottelo.config import get_credentials
from robottelo.config import get_url
from robottelo.config import setting_is_set
from robottelo.config import settings
from robottelo.config import user_nailgun_config
from robottelo.constants.repos import CUSTOM_RPM_REPO
from robottelo.utils.issue_handlers import is_open
from robottelo.utils.manifest import clone


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
    'alternate_content_sources': (
        '/katello/api/alternate_content_sources',
        '/katello/api/alternate_content_sources/:id',
        '/katello/api/alternate_content_sources',
        '/katello/api/alternate_content_sources/:id',
        '/katello/api/alternate_content_sources/:id',
        '/katello/api/alternate_content_sources/:id/refresh',
    ),
    'alternate_content_sources_bulk_actions': (
        '/katello/api/alternate_content_sources/bulk/destroy',
        '/katello/api/alternate_content_sources/bulk/refresh',
    ),
    'ansible_collections': (
        '/katello/api/ansible_collections',
        '/katello/api/ansible_collections/compare',
        '/katello/api/ansible_collections/:id',
    ),
    'ansible_inventories': (
        '/ansible/api/ansible_inventories/hosts',
        '/ansible/api/ansible_inventories/hostgroups',
        '/ansible/api/ansible_inventories/schedule',
    ),
    'ansible_override_values': (
        '/ansible/api/ansible_override_values',
        '/ansible/api/ansible_override_values/:id',
    ),
    'ansible_playbooks': (
        '/ansible/api/ansible_playbooks/fetch',
        '/ansible/api/ansible_playbooks/sync',
    ),
    'ansible_roles': (
        '/ansible/api/ansible_roles',
        '/ansible/api/ansible_roles/:id',
        '/ansible/api/ansible_roles/:id',
        '/ansible/api/ansible_roles/fetch',
        '/ansible/api/ansible_roles/import',
        '/ansible/api/ansible_roles/obsolete',
        '/ansible/api/ansible_roles/sync',
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
    'candlepin_dynflow_proxy': ('/katello/api/consumers/:id/profiles',),
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
        '/katello/api/capsules/:id/reclaim_space',
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
        '/api/compute_resources/:id/associate/:vm_id',
        '/api/compute_resources/:id/available_clusters',
        '/api/compute_resources/:id/available_clusters/:cluster_id/available_resource_pools',
        '/api/compute_resources/:id/available_flavors',
        '/api/compute_resources/:id/available_folders',
        '/api/compute_resources/:id/available_images',
        '/api/compute_resources/:id/available_networks',
        '/api/compute_resources/:id/available_security_groups',
        '/api/compute_resources/:id/available_storage_domains',
        '/api/compute_resources/:id/available_storage_pods',
        '/api/compute_resources/:id/available_vnic_profiles',
        '/api/compute_resources/:id/available_zones',
        '/api/compute_resources/:id/refresh_cache',
        '/api/compute_resources/:id/available_virtual_machines',
        '/api/compute_resources/:id/available_virtual_machines/:vm_id',
        '/api/compute_resources/:id/available_virtual_machines/:vm_id/power',
        '/api/compute_resources/:id/available_virtual_machines/:vm_id',
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
    'content_export_incrementals': (
        '/katello/api/content_export_incrementals/version',
        '/katello/api/content_export_incrementals/library',
        '/katello/api/content_export_incrementals/repository',
    ),
    'content_exports': (
        '/katello/api/content_exports',
        '/katello/api/content_exports/version',
        '/katello/api/content_exports/library',
        '/katello/api/content_exports/repository',
    ),
    'content_imports': (
        '/katello/api/content_imports',
        '/katello/api/content_imports/version',
        '/katello/api/content_imports/library',
        '/katello/api/content_imports/repository',
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
        '/katello/api/content_views/:content_view_id/filters/:id/remove_filter_rules',
        '/katello/api/content_views/:content_view_id/filters/:id/add_filter_rules',
    ),
    'content_views': (
        '/katello/api/content_views/:id',
        '/katello/api/content_views/:id',
        '/katello/api/content_views/:id',
        '/katello/api/content_views/:id/bulk_delete_versions',
        '/katello/api/content_views/:id/copy',
        '/katello/api/content_views/:id/environments/:environment_id',
        '/katello/api/content_views/:id/publish',
        '/katello/api/content_views/:id/remove',
        '/katello/api/content_views/:id/remove_filters',
        '/katello/api/organizations/:organization_id/content_views',
        '/katello/api/organizations/:organization_id/content_views',
    ),
    'content_view_histories': ('/katello/api/content_views/:id/history',),
    'content_view_versions': (
        '/katello/api/content_view_versions',
        '/katello/api/content_view_versions/:id',
        '/katello/api/content_view_versions/:id',
        '/katello/api/content_view_versions/:id',
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
    'docker_tags': (
        '/katello/api/docker_tags/compare',
        '/katello/api/docker_tags/:id',
        '/katello/api/docker_tags/:id/repositories',
    ),
    'domains': (
        '/api/domains',
        '/api/domains',
        '/api/domains/:id',
        '/api/domains/:id',
        '/api/domains/:id',
    ),
    'errata': (
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
    'file_units': ('/katello/api/files', '/katello/api/files/compare', '/katello/api/files/:id'),
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
        '/foreman_tasks/api/tasks/bulk_resume',
        '/foreman_tasks/api/tasks/bulk_cancel',
        '/foreman_tasks/api/tasks/bulk_stop',
        '/foreman_tasks/api/tasks/bulk_search',
        '/foreman_tasks/api/tasks/callback',
        '/foreman_tasks/api/tasks/summary',
    ),
    'generic_content_units': (
        '/katello/api/content_units',
        '/katello/api/content_units/:id',
        '/katello/api/content_units/compare',
        '/katello/api/ostree_refs',
    ),
    'home': ('/api', '/api/status'),
    'host_autocomplete': (),
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
    'host_statuses': ('/api/host_statuses',),
    'host_subscriptions': (
        '/api/hosts/:host_id/subscriptions',
        '/api/hosts/:host_id/subscriptions',
        '/api/hosts/:host_id/subscriptions/add_subscriptions',
        '/api/hosts/:host_id/subscriptions/auto_attach',
        '/api/hosts/:host_id/subscriptions/available_release_versions',
        '/api/hosts/:host_id/subscriptions/enabled_repositories',
        '/api/hosts/:host_id/subscriptions/content_override',
        '/api/hosts/:host_id/subscriptions/product_content',
        '/api/hosts/subscriptions',
    ),
    'host_tracer': (
        '/api/hosts/:host_id/traces',
        '/api/hosts/:host_id/traces/resolve',
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
        '/api/hosts/:id/status/:type',
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
        '/api/hosts/bulk/remove_host_collections',
        '/api/hosts/bulk/add_subscriptions',
        '/api/hosts/bulk/remove_subscriptions',
        '/api/hosts/bulk/auto_attach',
        '/api/hosts/bulk/applicable_errata',
        '/api/hosts/bulk/installable_errata',
        '/api/hosts/bulk/available_incremental_updates',
        '/api/hosts/bulk/content_overrides',
        '/api/hosts/bulk/change_content_source',
        '/api/hosts/bulk/destroy',
        '/api/hosts/bulk/environment_content_view',
        '/api/hosts/bulk/install_content',
        '/api/hosts/bulk/update_content',
        '/api/hosts/bulk/remove_content',
        '/api/hosts/bulk/module_streams',
        '/api/hosts/bulk/release_version',
        '/api/hosts/bulk/resolve_traces',
        '/api/hosts/bulk/traces',
        '/api/hosts/bulk/system_purpose',
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
    'instance_hosts': (
        '/api/instance_hosts',
        '/api/instance_hosts/:host_id',
        '/api/instance_hosts/:host_id',
    ),
    'inventory': (
        '/api/organizations/:organization_id/rh_cloud/report',
        '/api/organizations/:organization_id/rh_cloud/report',
        '/api/organizations/:organization_id/rh_cloud/inventory_sync',
        '/api/rh_cloud/enable_connector',
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
        '/api/job_invocations/:id/outputs',
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
    'mail_notifications': (
        '/api/mail_notifications',
        '/api/mail_notifications/:id',
        '/api/users/:user_id/mail_notifications',
        '/api/users/:user_id/mail_notifications/:mail_notification_id',
        '/api/users/:user_id/mail_notifications/:mail_notification_id',
        '/api/users/:user_id/mail_notifications',
    ),
    'media': (
        '/api/media',
        '/api/media',
        '/api/media/:id',
        '/api/media/:id',
        '/api/media/:id',
    ),
    'models': (
        '/api/models',
        '/api/models',
        '/api/models/:id',
        '/api/models/:id',
        '/api/models/:id',
    ),
    'module_streams': (
        '/katello/api/module_streams/compare',
        '/katello/api/module_streams/:id',
    ),
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
        '/katello/api/organizations/:id/redhat_provider',
        '/katello/api/organizations/:id/releases',
        '/katello/api/organizations/:id/repo_discover',
        '/katello/api/organizations/:label/cancel_repo_discover',
        '/katello/api/organizations/:label/download_debug_certificate',
        '/katello/api/organizations/:id/cdn_configuration',
    ),
    'os_default_templates': (
        '/api/operatingsystems/:operatingsystem_id/os_default_templates',
        '/api/operatingsystems/:operatingsystem_id/os_default_templates',
        '/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
        '/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
        '/api/operatingsystems/:operatingsystem_id/os_default_templates/:id',
    ),
    'oval_contents': (
        '/api/compliance/oval_contents',
        '/api/compliance/oval_contents/:id',
        '/api/compliance/oval_contents',
        '/api/compliance/oval_contents/:id',
        '/api/compliance/oval_contents/:id',
        '/api/compliance/oval_contents/sync',
    ),
    'oval_policies': (
        '/api/compliance/oval_policies',
        '/api/compliance/oval_policies/:id',
        '/api/compliance/oval_policies',
        '/api/compliance/oval_policies/:id',
        '/api/compliance/oval_policies/:id',
        '/api/compliance/oval_policies/:id/assign_hostgroups',
        '/api/compliance/oval_policies/:id/assign_hosts',
        '/api/compliance/oval_policies/:id/oval_content',
    ),
    'oval_reports': ('/api/compliance/oval_reports/:cname/:oval_policy_id/:date',),
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
    'preupgrade_reports': (
        '/api/preupgrade_reports',
        '/api/preupgrade_reports/:id',
        '/api/job_invocations/:id/preupgrade_reports',
    ),
    'products_bulk_actions': (
        '/katello/api/products/bulk/destroy',
        '/katello/api/products/bulk/http_proxy',
        '/katello/api/products/bulk/sync_plan',
        '/katello/api/products/bulk/verify_checksum',
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
        '/foreman_tasks/api/recurring_logics/bulk_destroy',
    ),
    'remote_execution_features': (
        '/api/remote_execution_features',
        '/api/remote_execution_features/:id',
        '/api/remote_execution_features/:id',
    ),
    'scap_content_profiles': ('/api/compliance/scap_content_profiles',),
    'simple_content_access': (
        '/katello/api/organizations/:organization_id/simple_content_access/eligible',
        '/katello/api/organizations/:organization_id/simple_content_access/enable',
        '/katello/api/organizations/:organization_id/simple_content_access/disable',
        '/katello/api/organizations/:organization_id/simple_content_access/status',
    ),
    'registration': ('/api/register', '/api/register'),
    'registration_commands': ('/api/registration_commands',),
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
        '/katello/api/repositories/bulk/reclaim_space',
    ),
    'repositories': (
        '/katello/api/repositories',
        '/katello/api/repositories',
        '/katello/api/repositories/:id',
        '/katello/api/repositories/:id',
        '/katello/api/repositories/:id',
        '/katello/api/repositories/:id/gpg_key_content',
        '/katello/api/repositories/:id/import_uploads',
        '/katello/api/repositories/:id/republish',
        '/katello/api/repositories/:id/sync',
        '/katello/api/repositories/:id/upload_content',
        '/katello/api/repositories/repository_types',
        '/katello/api/repositories/:id/verify_checksum',
        '/katello/api/content_types',
        '/katello/api/repositories/:id/reclaim_space',
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
        '/api/compliance/scap_contents/bulk_upload',
    ),
    'settings': ('/api/settings', '/api/settings/:id', '/api/settings/:id'),
    'smart_proxies': (
        '/api/smart_proxies',
        '/api/smart_proxies',
        '/api/smart_proxies/:id',
        '/api/smart_proxies/:id',
        '/api/smart_proxies/:id',
        '/api/smart_proxies/:id/import_subnets',
        '/api/smart_proxies/:id/refresh',
    ),
    'smart_proxy_hosts': (
        '/api/smart_proxies/:smart_proxy_id/hosts',
        '/api/smart_proxies/:smart_proxy_id/hosts/:host_id',
        '/api/smart_proxies/:smart_proxy_id/hosts/:host_id',
    ),
    'srpms': ('/katello/api/srpms/:id', '/katello/api/srpms/compare'),
    'ssh_keys': (
        '/api/users/:user_id/ssh_keys',
        '/api/users/:user_id/ssh_keys',
        '/api/users/:user_id/ssh_keys/:id',
        '/api/users/:user_id/ssh_keys/:id',
    ),
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
    'templates': ('/api/templates/export', '/api/templates/import'),
    'template_combinations': (
        '/api/provisioning_templates/:provisioning_template_id/template_combinations',
        '/api/provisioning_templates/:provisioning_template_id/template_combinations',
        '/api/template_combinations/:id',
        '/api/provisioning_templates/:provisioning_template_id/template_combinations/:id',
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
    'upstream_subscriptions': (
        '/katello/api/organizations/:organization_id/upstream_subscriptions',
        '/katello/api/organizations/:organization_id/upstream_subscriptions',
        '/katello/api/organizations/:organization_id/upstream_subscriptions',
        '/katello/api/organizations/:organization_id/upstream_subscriptions',
        '/katello/api/organizations/:organization_id/upstream_subscriptions/ping',
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
    'webhooks': (
        '/api/webhooks',
        '/api/webhooks/:id',
        '/api/webhooks',
        '/api/webhooks/:id',
        '/api/webhooks/:id',
        '/api/webhooks/events',
    ),
    'webhook_templates': (
        '/api/webhook_templates',
        '/api/webhook_templates/:id',
        '/api/webhook_templates',
        '/api/webhook_templates/import',
        '/api/webhook_templates/:id',
        '/api/webhook_templates/:id',
        '/api/webhook_templates/:id/clone',
        '/api/webhook_templates/:id/export',
    ),
}


@pytest.fixture(scope='module', autouse=True)
def filtered_api_paths():
    """Filter the API_PATHS dict based on BZs that impact various endpoints"""
    missing = defaultdict(list)
    if is_open('BZ:1887932'):
        missing['subscriptions'].append(
            '/katello/api/activation_keys/:activation_key_id/subscriptions'
        )
    filtered_paths = API_PATHS.copy()
    for endpoint, missing_paths in missing.items():
        filtered_paths[endpoint] = tuple(
            path for path in filtered_paths[endpoint] if path not in missing_paths
        )
    return filtered_paths


class TestAvailableURLs:
    """Tests for ``api/v2``."""

    pytestmark = [pytest.mark.tier1, pytest.mark.upgrade]

    @pytest.fixture(scope='class')
    def api_url(self):
        """We want to delay referencing get_url() until test execution"""
        return f'{get_url()}/api/v2'

    @pytest.mark.build_sanity
    def test_positive_get_status_code(self, api_url):
        """GET ``api/v2`` and examine the response.

        :id: 9d9c1afd-9158-419e-9a6e-91e9888f0c04

        :expectedresults: HTTP 200 is returned with an ``application/json``
            content-type

        """
        response = client.get(api_url, auth=get_credentials(), verify=False)
        assert response.status_code == http.client.OK
        assert 'application/json' in response.headers['content-type']

    def test_positive_get_links(self, api_url, filtered_api_paths):
        """GET ``api/v2`` and check the links returned.

        :id: 7b2dd77a-a821-485b-94db-b583f93c9a89

        :expectedresults: The paths returned are equal to ``API_PATHS``.

        """
        # Did the server give us any paths at all?
        response = client.get(api_url, auth=get_credentials(), verify=False)
        response.raise_for_status()
        # response.json()['links'] is a dict like this:
        #
        #     {'content_views': {
        #          '…': '/katello/api/content_views/:id',
        #          '…': '/katello/api/organizations/:organization_id/content_views',
        #          '…': '/katello/api/organizations/:organization_id/content_views',
        #     }, …}
        #
        # We don't care about prose descriptions. It doesn't matter if those
        # change. Transform it before running any assertions:
        #
        #     {'content_views': [
        #          '/katello/api/content_views/:id',
        #          '/katello/api/organizations/:organization_id/content_views',
        #          '/katello/api/organizations/:organization_id/content_views',
        #     ], …}
        sat_api_paths = response.json()['links']
        transformed_paths = {ep: tuple(paths.values()) for ep, paths in sat_api_paths.items()}
        api_diff = DeepDiff(
            filtered_api_paths,
            transformed_paths,
            ignore_order=True,
            report_repetition=True,
            verbose_level=0,
        )
        assert api_diff == {}, f'API path mismatch (expected first): \n{pformat(api_diff)}'


class TestEndToEnd:
    """End-to-end tests using the ``API`` path."""

    pytestmark = [pytest.mark.tier1, pytest.mark.upgrade]

    @pytest.fixture(scope='class')
    def fake_manifest_is_set(self):
        return setting_is_set('fake_manifest')

    @pytest.mark.build_sanity
    def test_positive_find_default_org(self):
        """Check if 'Default Organization' is present

        :id: c6e45b36-d8b6-4507-8dcd-0645668496b9

        :expectedresults: 'Default Organization' is found
        """
        results = entities.Organization().search(
            query={'search': f'name="{constants.DEFAULT_ORG}"'}
        )
        assert len(results) == 1
        assert results[0].name == constants.DEFAULT_ORG

    @pytest.mark.build_sanity
    def test_positive_find_default_loc(self):
        """Check if 'Default Location' is present

        :id: 1f40b3c6-488d-4037-a7ab-250a02bf919a

        :expectedresults: 'Default Location' is found
        """
        results = entities.Location().search(query={'search': f'name="{constants.DEFAULT_LOC}"'})
        assert len(results) == 1
        assert results[0].name == constants.DEFAULT_LOC

    @pytest.mark.build_sanity
    def test_positive_find_admin_user(self):
        """Check if Admin User is present

        :id: 892fdfcd-18c0-42ef-988b-f13a04097f5c

        :expectedresults: Admin User is found and has Admin role
        """
        results = entities.User().search(query={'search': 'login=admin'})
        assert len(results) == 1
        assert results[0].login == 'admin'

    @pytest.mark.skip_if_not_set('libvirt')
    @pytest.mark.tier4
    @pytest.mark.e2e
    @pytest.mark.upgrade
    @pytest.mark.skipif(
        (not settings.robottelo.REPOS_HOSTING_URL), reason='Missing repos_hosting_url'
    )
    def test_positive_end_to_end(self, fake_manifest_is_set, target_sat, rhel7_contenthost):
        """Perform end to end smoke tests using RH and custom repos.

        1. Create a new user with admin permissions
        2. Using the new user from above
            1. Create a new organization
            2. Clone and upload manifest
            3. Create a new lifecycle environment
            4. Create a custom product
            5. Create a custom YUM repository
            6. Enable a Red Hat repository
            7. Synchronize these two repositories
            8. Create a new content view
            9. Associate the YUM and Red Hat repositories to new content view
            10. Publish content view
            11. Promote content view to the lifecycle environment
            12. Create a new activation key
            13. Add the products to the activation key
            14. Create a new libvirt compute resource
            15. Create a new subnet
            16. Create a new domain
            17. Create a new hostgroup and associate previous entities to it
            18. Provision a client  **  NOT CURRENTLY PROVISIONING

        :id: b2f73740-d3ce-4e6e-abc7-b23e5562bac1

        :expectedresults: All tests should succeed and Content should be
            successfully fetched by client.

        :parametrized: yes
        """
        # step 1: Create a new user with admin permissions
        login = gen_string('alphanumeric')
        password = gen_string('alphanumeric')
        target_sat.api.User(admin=True, login=login, password=password).create()

        # step 2.1: Create a new organization
        user_cfg = user_nailgun_config(login, password)
        org = target_sat.api.Organization(server_config=user_cfg).create()

        # step 2.2: Clone and upload manifest
        if fake_manifest_is_set:
            with clone() as manifest:
                target_sat.upload_manifest(org.id, manifest.content)

        # step 2.3: Create a new lifecycle environment
        le1 = target_sat.api.LifecycleEnvironment(server_config=user_cfg, organization=org).create()

        # step 2.4: Create a custom product
        prod = target_sat.api.Product(server_config=user_cfg, organization=org).create()
        repositories = []

        # step 2.5: Create custom YUM repository
        custom_repo = target_sat.api.Repository(
            server_config=user_cfg, product=prod, content_type='yum', url=CUSTOM_RPM_REPO
        ).create()
        repositories.append(custom_repo)

        # step 2.6: Enable a Red Hat repository
        if fake_manifest_is_set:
            rhel_repo = target_sat.api.Repository(
                id=enable_rhrepo_and_fetchid(
                    basearch='x86_64',
                    org_id=org.id,
                    product=constants.PRDS['rhel'],
                    repo=constants.REPOS['rhst7']['name'],
                    reposet=constants.REPOSET['rhst7'],
                )
            )
            repositories.append(rhel_repo)

        # step 2.7: Synchronize these two repositories
        for repo in repositories:
            repo.sync()

        # step 2.8: Create content view
        content_view = target_sat.api.ContentView(server_config=user_cfg, organization=org).create()

        # step 2.9: Associate the YUM and Red Hat repositories to new content view
        content_view.repository = repositories
        content_view = content_view.update(['repository'])

        # step 2.10: Publish content view
        content_view.publish()

        # step 2.11: Promote content view to the lifecycle environment
        content_view = content_view.read()
        assert len(content_view.version) == 1
        cv_version = content_view.version[0].read()
        assert len(cv_version.environment) == 1
        cv_version.promote(data={'environment_ids': le1.id})
        # check that content view exists in lifecycle
        content_view = content_view.read()
        assert len(content_view.version) == 1
        cv_version = cv_version.read()

        # step 2.12: Create a new activation key
        activation_key_name = gen_string('alpha')
        activation_key = target_sat.api.ActivationKey(
            name=activation_key_name, environment=le1, organization=org, content_view=content_view
        ).create()

        # step 2.13: Add the products to the activation key
        for sub in target_sat.api.Subscription(organization=org).search():
            if sub.name == constants.DEFAULT_SUBSCRIPTION_NAME:
                activation_key.add_subscriptions(data={'quantity': 1, 'subscription_id': sub.id})
                break
        # step 2.13.1: Enable product content
        if fake_manifest_is_set:
            activation_key.content_override(
                data={
                    'content_overrides': [
                        {'content_label': constants.REPOS['rhst7']['id'], 'value': '1'}
                    ]
                }
            )

        # BONUS: Create a content host and associate it with promoted
        # content view and last lifecycle where it exists
        content_host = target_sat.api.Host(
            content_facet_attributes={
                'content_view_id': content_view.id,
                'lifecycle_environment_id': le1.id,
            },
            organization=org,
        ).create()
        # check that content view matches what we passed
        assert content_host.content_facet_attributes['content_view_id'] == content_view.id
        # check that lifecycle environment matches
        assert content_host.content_facet_attributes['lifecycle_environment_id'] == le1.id

        # step 2.14: Create a new libvirt compute resource
        target_sat.api.LibvirtComputeResource(
            server_config=user_cfg,
            url=f'qemu+ssh://root@{settings.libvirt.libvirt_hostname}/system',
        ).create()

        # step 2.15: Create a new subnet
        subnet = target_sat.api.Subnet(server_config=user_cfg).create()

        # step 2.16: Create a new domain
        domain = target_sat.api.Domain(server_config=user_cfg).create()

        # step 2.17: Create a new hostgroup and associate previous entities to it
        target_sat.api.HostGroup(server_config=user_cfg, domain=domain, subnet=subnet).create()

        # step 2.18: Provision a client
        # TODO this isn't provisioning through satellite as intended
        # Note it wasn't well before the change that added this todo
        rhel7_contenthost.install_katello_ca(target_sat)
        # Register client with foreman server using act keys
        rhel7_contenthost.register_contenthost(org.label, activation_key_name)
        assert rhel7_contenthost.subscribed
        # Install rpm on client
        package_name = 'katello-agent'
        result = rhel7_contenthost.execute(f'yum install -y {package_name}')
        assert result.status == 0
        # Verify that the package is installed by querying it
        result = rhel7_contenthost.run(f'rpm -q {package_name}')
        assert result.status == 0
