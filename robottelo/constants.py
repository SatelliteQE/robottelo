# -*- encoding: utf-8 -*-
"""
Defines various constants
"""

# Bugzilla
BZ_OPEN_STATUSES = [
    'NEW',
    'ASSIGNED',
    'POST',
    'MODIFIED'
]
BZ_CLOSED_STATUSES = [
    'ON_QA',
    'VERIFIED',
    'RELEASE_PENDING',
    'CLOSED'
]
ROBOTTELO_PROPERTIES = "robottelo.properties"

FOREMAN_PROVIDERS = {
    'libvirt': 'Libvirt',
    'rhev': 'RHEV',
    'ec2': 'EC2',
    'vmware': 'VMWare',
    'openstack': 'RHEL OpenStack Platform',
    'rackspace': 'Rackspace',
    'google': 'Google',
    'docker': 'Docker',
}

LIBVIRT_RESOURCE_URL = 'qemu+tcp://%s:16509/system'


HTML_TAGS = [
    'A', 'ABBR', 'ACRONYM', 'ADDRESS', 'APPLET', 'AREA', 'B',
    'BASE', 'BASEFONT', 'BDO', 'BIG', 'BLINK', 'BLOCKQUOTE', 'BODY', 'BR',
    'BUTTON', 'CAPTION', 'CENTER', 'CITE', 'CODE', 'COL', 'COLGROUP',
    'DD', 'DEL', 'DFN', 'DIR', 'DIV', 'DL', 'DT',
    'EM', 'FIELDSET', 'FONT', 'FORM', 'FRAME', 'FRAMESET', 'H1',
    'H2', 'H3', 'H4', 'H5', 'H6', 'HEAD', 'HR',
    'HTML', 'I', 'IFRAME', 'IMG', 'INPUT', 'INS', 'ISINDEX',
    'KBD', 'LABEL', 'LEGEND', 'LI', 'LINK', 'MAP', 'MENU',
    'META', 'NOFRAMES', 'NOSCRIPT', 'OBJECT', 'OL', 'OPTGROUP', 'OPTION',
    'P', 'PARAM', 'PRE', 'Q', 'S', 'SAMP', 'SCRIPT',
    'SELECT', 'SMALL', 'SPAN', 'STRIKE', 'STRONG', 'STYLE', 'SUB',
    'SUP', 'TABLE', 'TBODY', 'TD', 'TEXTAREA', 'TFOOT', 'TH',
    'THEAD', 'TITLE', 'TR', 'TT', 'U', 'UL', 'VAR']

OPERATING_SYSTEMS = [
    'AIX',
    'Archlinux',
    'Debian',
    'Freebsd',
    'Gentoo',
    'Redhat',
    'Solaris',
    'Suse',
    'Windows',
]

TEMPLATE_TYPES = [
    'finish',
    'iPXE',
    'provision',
    'PXEGrub',
    'PXELinux',
    'script',
    'user_data',
    'ZTP'
]

#       NOTE:- Below unique filter key's are used for select-item box
#       filter's common_locator['filter']
FILTER = {
    'arch_os': 'architecture_operatingsystem',
    'cr_loc': 'compute_resource_location',
    'cr_org': 'compute_resource_organization',
    'env_org': 'environment_organization',
    'loc_domain': 'location_domain',
    'loc_envs': 'location_environment',
    'loc_hostgroup': 'location_hostgroup',
    'loc_media': 'location_medium',
    'loc_org': 'location_organization',
    'loc_proxy': 'location_smart_proxy',
    'loc_resource': 'location_compute_resource',
    'loc_subnet': 'location_subnet',
    'loc_template': 'location_config_template',
    'loc_user': 'location_user',
    'location_user': 'location_user',
    'org_domain': 'organization_domain',
    'org_envs': 'organization_environment',
    'org_hostgroup': 'organization_hostgroup',
    'org_location': 'organization_location',
    'org_media': 'organization_medium',
    'org_proxy': 'organization_smart_proxy',
    'org_resource': 'organization_compute_resource',
    'org_subnet': 'organization_subnet',
    'org_template': 'organization_config_template',
    'org_user': 'organization_user',
    'os_arch': 'operatingsystem_architecture',
    'os_medium': 'operatingsystem_medium',
    'os_ptable': 'operatingsystem_ptable',
    'oscap_loc': 'scap_content_location',
    'oscap_org': 'scap_content_organization',
    'policy_loc': 'policy_location',
    'policy_org': 'policy_organization',
    'policy_hgrp': 'policy_hostgroup',
    'reg_loc': 'docker_registry_location',
    'reg_org': 'docker_registry_organization',
    'role_org': 'filter_organization',
    'role_permission': 'filter_permission',
    'sub_domain': 'subnet_domain',
    'subnet_org': 'subnet_organization',
    'template_os': 'config_template_operatingsystem',
    'user_location': 'user_location',
    'user_org': 'user_organization',
    'user_role': 'user_role',
    'usergroup_user': 'usergroup_user',
    'usergroup_role': "usergroup_role",
}

RESOURCE_DEFAULT = 'Bare Metal'

OS_TEMPLATE_DATA_FILE = "os_template.txt"

DOMAIN = "lab.dom.%s.com"

PARTITION_SCRIPT_DATA_FILE = "partition_script.txt"

SNIPPET_DATA_FILE = "snippet.txt"

SNIPPET_URL = 'https://gist.github.com/sghai/8434467/raw'

INSTALL_MEDIUM_URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"

VALID_GPG_KEY_FILE = "valid_gpg_key.txt"

ZOO_CUSTOM_GPG_KEY = "zoo_custom_gpgkey.txt"

VALID_GPG_KEY_BETA_FILE = "valid_gpg_key_beta.txt"

RPM_TO_UPLOAD = "which-2.19-6.el6.x86_64.rpm"

ENVIRONMENT = "Library"

NOT_IMPLEMENTED = 'Test not implemented'

SYNC_INTERVAL = {'hour': "hourly",
                 'day': "daily",
                 'week': "weekly"}

REPO_TYPE = {
    'yum': "yum",
    'puppet': "puppet",
    'docker': "docker",
}

CHECKSUM_TYPE = {
    'default': "Default",
    'sha256': "sha256",
    'sha1': "sha1",
}

# On importing manifests, Red Hat repositories are listed like this:
# Product -> RepositorySet -> Repository
# We need to first select the Product, then the reposet and then the repos
# Example: 'rhel' is the name of Product that contains following REPOSETs
PRDS = {
    'rhcf': 'Red Hat CloudForms',
    'rhel': 'Red Hat Enterprise Linux Server',
}

REPOSET = {
    'rhct6': 'Red Hat CloudForms Tools for RHEL 6 (RPMs)',
    'rhel6': 'Red Hat Enterprise Linux 6 Server (RPMs)',
    'rhva6': (
        'Red Hat Enterprise Virtualization Agents for RHEL 6 Server (RPMs)'
    ),
    'rhst7': 'Red Hat Satellite Tools 6.1 (for RHEL 7 Server) (RPMs)',
    'rhst6': 'Red Hat Satellite Tools 6.1 (for RHEL 6 Server) (RPMs)',
}

REPOS = {
    'rhst7': {
        'id': 'rhel-7-server-satellite-tools-6.1-rpms',
        'name': (
            'Red Hat Satellite Tools 6.1 for RHEL 7 Server RPMs x86_64'
        ),
    },
    'rhst6': {
        'id': 'rhel-6-server-satellite-tools-6.1-rpms',
        'name': (
            'Red Hat Satellite Tools 6.1 for RHEL 6 Server RPMs x86_64'
        ),
    },
    'rhva6': {
        'name': (
            'Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs '
            'x86_64 6Server'
        ),
    },
    'rhva65': {
        'name': (
            'Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs '
            'x86_64 6.5'
        ),
    },
}

PRD_SETS = {
    'rhel_66': {
        'product': u'Red Hat Enterprise Linux Server',
        'reposet': u'Red Hat Enterprise Linux 6 Server (RPMs)',
        'reponame': u'Red Hat Enterprise Linux 6 Server RPMs x86_64 6.7',
        'arch': u'x86_64',
        'releasever': u'6.7',
        'label': u'rhel-6-server-rpms'
    },
    'rhel6_sat6tools': {
        'product': u'Red Hat Enterprise Linux Server',
        'reposet': u'Red Hat Satellite Tools 6.1 (for RHEL 6 Server) '
                   '(RPMs)',
        'reponame': u'Red Hat Satellite Tools 6.1 for RHEL 6 Server RPMs '
                    'x86_64',
        'arch': u'x86_64',
        'releasever': None,
        'label': u'rhel-6-server-satellite-tools-6.1-rpms'
    }
}

# The 'create_repos_tree' function under 'sync' module uses the following
# list of tuples. It actually includes following two repos under
# Reposet: Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs
#
# Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs x86_64 6.5
# Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs x86_64
# 6Server

RHVA_REPO_TREE = [
    ('rhel', 'rhva6', 'rhva65', 'repo_name',
     'Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs '
     'x86_64 6.5'),
    ('rhel', 'rhva6', 'rhva65', 'repo_arch', 'x86_64'),
    ('rhel', 'rhva6', 'rhva65', 'repo_ver', '6.5'),
    ('rhel', 'rhva6', 'rhva6S', 'repo_name',
     'Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs '
     'x86_64 6Server'),
    ('rhel', 'rhva6', 'rhva6S', 'repo_arch', 'x86_64'),
    ('rhel', 'rhva6', 'rhva6S', 'repo_ver', '6Server')
]

SAT6_TOOLS_TREE = [
    ('rhel', 'rhst6', 'rhst6', 'repo_name',
     'Red Hat Satellite Tools 6.1 for RHEL 6 Server RPMs x86_64'),
    ('rhel', 'rhst6', 'rhst6', 'repo_arch', 'x86_64'),
    ('rhel', 'rhst6', 'rhst6', 'repo_ver', '6.1'),
]

#: Name (not label!) of the default organization.
DEFAULT_ORG = "Default Organization"
#: Name (not label!) of the default location.
DEFAULT_LOC = "Default Location"
DEFAULT_CV = "Default Organization View"
DEFAULT_SUBSCRIPTION_NAME = 'Employee SKU'

LANGUAGES = ["en", "en_GB",
             "fr", "gl",
             "ja", "sv_SE"]

FILTER_CONTENT_TYPE = {
    'package': "Package",
    'package group': "Package Group",
    'erratum by id': "Erratum - by ID",
    'erratum by date and type': "Erratum - by Date and Type"}

FILTER_TYPE = {'include': "Include",
               'exclude': "Exclude"}

DOCKER_REGISTRY_HUB = u'https://registry.hub.docker.com/'
GOOGLE_CHROME_REPO = u'http://dl.google.com/linux/chrome/rpm/stable/x86_64'
FAKE_0_YUM_REPO = "http://inecas.fedorapeople.org/fakerepos/zoo/"
FAKE_1_YUM_REPO = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
FAKE_2_YUM_REPO = "http://inecas.fedorapeople.org/fakerepos/zoo2/"
FAKE_3_YUM_REPO = "http://omaciel.fedorapeople.org/fakerepo01"
FAKE_4_YUM_REPO = "http://omaciel.fedorapeople.org/fakerepo02"
FAKE_0_PUPPET_REPO = u'http://davidd.fedorapeople.org/repos/random_puppet/'
FAKE_1_PUPPET_REPO = "http://omaciel.fedorapeople.org/fakepuppet01"
FAKE_2_PUPPET_REPO = "http://omaciel.fedorapeople.org/fakepuppet02"
FAKE_3_PUPPET_REPO = "http://omaciel.fedorapeople.org/fakepuppet03"
FAKE_4_PUPPET_REPO = "http://omaciel.fedorapeople.org/fakepuppet04"
FAKE_5_PUPPET_REPO = "http://omaciel.fedorapeople.org/fakepuppet05"
FAKE_6_PUPPET_REPO = "http://kbidarka.fedorapeople.org/repos/puppet-modules/"
REPO_DISCOVERY_URL = "http://omaciel.fedorapeople.org/"
FAKE_0_CUSTOM_PACKAGE = 'bear-4.1-1.noarch'
FAKE_0_CUSTOM_PACKAGE_NAME = 'bear'
FAKE_1_CUSTOM_PACKAGE = 'walrus-0.71-1.noarch'
FAKE_1_CUSTOM_PACKAGE_NAME = 'walrus'
FAKE_2_CUSTOM_PACKAGE = 'walrus-5.21-1.noarch'
FAKE_2_CUSTOM_PACKAGE_NAME = 'walrus'
FAKE_0_CUSTOM_PACKAGE_GROUP_NAME = 'birds'
FAKE_0_ERRATA_ID = 'RHEA-2012:0001'

PUPPET_MODULE_NTP_PUPPETLABS = "puppetlabs-ntp-3.2.1.tar.gz"

FAKE_0_CUSTOM_PACKAGE_GROUP = [
    'cockateel-3.1-1.noarch',
    'duck-0.6-1.noarch',
    'penguin-0.9.1-1.noarch',
    'stork-0.12-2.noarch',
]

#: All permissions exposed by the server.
#: :mod:`tests.foreman.api.test_permission` makes use of this.
PERMISSIONS = {
    None: [
        'access_dashboard',
        'access_settings',
        'app_root',
        'attachments',
        'commit_containers',
        'configuration',
        'create_containers',
        'create_registries',
        'destroy_containers',
        'destroy_registries',
        'download_bootdisk',
        'edit_compliance',
        'logs',
        'my_organizations',
        'rh_telemetry_api',
        'rh_telemetry_configurations',
        'rh_telemetry_view',
        'search_repository_image_search',
        'view_arf_reports',
        'view_cases',
        'view_containers',
        'view_log_viewer',
        'view_plugins',
        'view_registries',
        'view_search',
        'view_statistics',
        'view_tasks',
    ],
    'Architecture': [
        'view_architectures',
        'create_architectures',
        'edit_architectures',
        'destroy_architectures',
    ],
    'Audit': [
        'view_audit_logs',
    ],
    'AuthSourceLdap': [
        'view_authenticators',
        'create_authenticators',
        'edit_authenticators',
        'destroy_authenticators',
    ],
    'Bookmark': [
        'view_bookmarks',
        'create_bookmarks',
        'edit_bookmarks',
        'destroy_bookmarks',
    ],
    'ConfigGroup': [
        'view_config_groups',
        'create_config_groups',
        'edit_config_groups',
        'destroy_config_groups',
    ],
    'Container': [
        'commit_containers',
        'create_containers',
        'destroy_containers',
        'view_containers',
    ],
    'ComputeProfile': [
        'view_compute_profiles',
        'create_compute_profiles',
        'edit_compute_profiles',
        'destroy_compute_profiles',
    ],
    'ComputeResource': [
        'view_compute_resources',
        'create_compute_resources',
        'edit_compute_resources',
        'destroy_compute_resources',
        'view_compute_resources_vms',
        'create_compute_resources_vms',
        'edit_compute_resources_vms',
        'destroy_compute_resources_vms',
        'power_compute_resources_vms',
        'console_compute_resources_vms',
    ],
    'ConfigTemplate': [
        'view_templates',
        'create_templates',
        'edit_templates',
        'destroy_templates',
        'deploy_templates',
        'lock_templates',
    ],
    'DiscoveryRule': [
        'create_discovery_rules',
        'destroy_discovery_rules',
        'edit_discovery_rules',
        'execute_discovery_rules',
        'view_discovery_rules',
    ],
    'Docker/ImageSearch': [
        'search_repository_image_search',
    ],
    'DockerRegistry': [
        'create_registries',
        'destroy_registries',
        'view_registries',
    ],
    'Domain': [
        'view_domains',
        'create_domains',
        'edit_domains',
        'destroy_domains',
    ],
    'Environment': [
        'view_environments',
        'create_environments',
        'edit_environments',
        'destroy_environments',
        'import_environments',
    ],
    'ExternalUsergroups': [
        'view_external_usergroups',
        'create_external_usergroups',
        'edit_external_usergroups',
        'destroy_external_usergroups',
    ],
    'LookupKey': [
        'view_external_variables',
        'create_external_variables',
        'edit_external_variables',
        'destroy_external_variables',
    ],
    'FactValue': [
        'view_facts',
        'upload_facts',
    ],
    'Filter': [
        'view_filters',
        'create_filters',
        'edit_filters',
        'destroy_filters',
    ],
    'ForemanTasks::Task': [
        u'edit_foreman_tasks',
        u'view_foreman_tasks',
    ],
    'CommonParameter': [
        'view_globals',
        'create_globals',
        'edit_globals',
        'destroy_globals',
    ],
    'HostClass': [
        'edit_classes',
    ],
    'Parameter': [
        'create_params',
        'edit_params',
        'destroy_params',
    ],
    'Hostgroup': [
        'view_hostgroups',
        'create_hostgroups',
        'edit_hostgroups',
        'destroy_hostgroups',
    ],
    'Image': [
        'view_images',
        'create_images',
        'edit_images',
        'destroy_images',
    ],
    'Location': [
        'view_locations',
        'create_locations',
        'edit_locations',
        'destroy_locations',
        'assign_locations',
    ],
    'MailNotification': [
        'view_mail_notifications',
    ],
    'Medium': [
        'view_media',
        'create_media',
        'edit_media',
        'destroy_media',
    ],
    'Model': [
        'view_models',
        'create_models',
        'edit_models',
        'destroy_models',
    ],
    'Operatingsystem': [
        'view_operatingsystems',
        'create_operatingsystems',
        'edit_operatingsystems',
        'destroy_operatingsystems',
    ],
    'Ptable': [
        'view_ptables',
        'create_ptables',
        'edit_ptables',
        'destroy_ptables',
    ],
    'Puppetclass': [
        'view_puppetclasses',
        'create_puppetclasses',
        'edit_puppetclasses',
        'destroy_puppetclasses',
        'import_puppetclasses',
    ],
    'Realm': [
        'view_realms',
        'create_realms',
        'edit_realms',
        'destroy_realms',
    ],
    'Report': [
        'view_reports',
        'destroy_reports',
        'upload_reports',
    ],
    'Role': [
        'view_roles',
        'create_roles',
        'edit_roles',
        'destroy_roles',
    ],
    'SmartProxy': [
        'view_smart_proxies',
        'create_smart_proxies',
        'edit_smart_proxies',
        'destroy_smart_proxies',
        'view_smart_proxies_autosign',
        'create_smart_proxies_autosign',
        'destroy_smart_proxies_autosign',
        'view_smart_proxies_puppetca',
        'edit_smart_proxies_puppetca',
        'destroy_smart_proxies_puppetca',
        'manage_capsule_content',
    ],
    'Subnet': [
        'view_subnets',
        'create_subnets',
        'edit_subnets',
        'destroy_subnets',
        'import_subnets',
    ],
    'Trend': [
        'view_trends',
        'create_trends',
        'edit_trends',
        'destroy_trends',
        'update_trends',
    ],
    'Usergroup': [
        'view_usergroups',
        'create_usergroups',
        'edit_usergroups',
        'destroy_usergroups',
    ],
    'User': [
        'view_users',
        'create_users',
        'edit_users',
        'destroy_users',
    ],
    'Host': [
        'auto_provision_discovered_hosts',
        'build_hosts',
        'console_hosts',
        'create_hosts',
        'destroy_discovered_hosts',
        'destroy_hosts',
        'edit_discovered_hosts',
        'edit_hosts',
        'ipmi_boot',
        'power_hosts',
        'provision_discovered_hosts',
        'puppetrun_hosts',
        'submit_discovered_hosts',
        'view_discovered_hosts',
        'view_hosts',
    ],
    'Katello::ActivationKey': [
        'view_activation_keys',
        'create_activation_keys',
        'edit_activation_keys',
        'destroy_activation_keys',
    ],
    'Katello::System': [
        'view_content_hosts',
        'create_content_hosts',
        'edit_content_hosts',
        'destroy_content_hosts',
    ],
    'Katello::ContentView': [
        'view_content_views',
        'create_content_views',
        'edit_content_views',
        'destroy_content_views',
        'publish_content_views',
        'promote_or_remove_content_views',
    ],
    'Katello::GpgKey': [
        'view_gpg_keys',
        'create_gpg_keys',
        'edit_gpg_keys',
        'destroy_gpg_keys',
    ],
    'Katello::HostCollection': [
        'view_host_collections',
        'create_host_collections',
        'edit_host_collections',
        'destroy_host_collections',
    ],
    'Katello::KTEnvironment': [
        'view_lifecycle_environments',
        'create_lifecycle_environments',
        'edit_lifecycle_environments',
        'destroy_lifecycle_environments',
        'promote_or_remove_content_views_to_environments',
    ],
    'Katello::Product': [
        'view_products',
        'create_products',
        'edit_products',
        'destroy_products',
        'sync_products',
    ],
    'Organization': [
        'view_organizations',
        'create_organizations',
        'edit_organizations',
        'destroy_organizations',
        'assign_organizations',
        'view_subscriptions',
        'attach_subscriptions',
        'unattach_subscriptions',
        'import_manifest',
        'delete_manifest',
    ],
    'Katello::SyncPlan': [
        'view_sync_plans',
        'create_sync_plans',
        'edit_sync_plans',
        'destroy_sync_plans',
    ],
}

ANY_CONTEXT = {'org': "Any Organization",
               'location': "Any Location"}

SUBNET_IPAM_TYPES = {
    'dhcp': 'DHCP',
    'internal': 'Internal DB',
    'none': 'None',
}

TREND_TYPES = {
    'environment': 'Environment',
    'os': 'Operating system',
    'model': 'Model',
    'facts': 'Facts',
    'host_group': 'Host group',
    'compute_resource': 'Compute resource',
}

LDAP_SERVER_TYPE = {
    'API': {
        'ipa': 'free_ipa',
        'ad': 'active_directory',
        'posix': 'posix',
    },
    'UI': {
        'ipa': 'FreeIPA',
        'ad': 'Active Directory',
        'posix': 'POSIX',
    },
}

LDAP_ATTR = {
    'login_ad': 'sAMAccountName',
    'login': 'uid',
    'firstname': 'givenName',
    'surname': 'sn',
    'mail': 'mail',
}

OSCAP_PERIOD = {
    'weekly': 'Weekly',
    'monthly': 'Monthly',
    'custom': 'Custom',
}

OSCAP_WEEKDAY = {
    'sunday': 'Sunday',
    'monday': 'Monday',
    'tuesday': 'Tuesday',
    'wednesday': 'Wednesday',
    'thursday': 'Thursday',
    'friday': 'Friday',
    'saturday': 'Saturday',
}

OSCAP_DEFAULT_CONTENT = {
    'rhel6_content': 'Red Hat rhel6 default content',
    'rhel7_content': 'Red Hat rhel7 default content',
}

OSCAP_PROFILE = {
    'c2s_rhel6': 'C2S for Red Hat Enterprise Linux 6',
    'rhccp': ('Red Hat Corporate Profile for '
              'Certified Cloud Providers (RH CCP)'),
    'usgcb': 'United States Government Configuration Baseline (USGCB)',
}
