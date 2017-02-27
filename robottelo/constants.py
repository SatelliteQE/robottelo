# -*- encoding: utf-8 -*-
"""Defines various constants"""
from nailgun import entities

LOCALES = (
    'ca', 'de', 'en', 'en_GB', 'es', 'fr', 'gl', 'it', 'ja', 'ko',
    'pt_BR', 'ru', 'sv_SE', 'zh_CN', 'zh_TW'
)

# Bugzilla / redmine
BUGZILLA_URL = "https://bugzilla.redhat.com/xmlrpc.cgi"
REDMINE_URL = 'http://projects.theforeman.org'

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

DISTRO_RHEL6 = "rhel6"
DISTRO_RHEL7 = "rhel7"

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

LIBVIRT_RESOURCE_URL = 'qemu+ssh://root@%s/system'

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

OPERATING_SYSTEMS = entities._OPERATING_SYSTEMS

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
    'container_loc': 'docker_container_wizard_states_preliminary_location',
    'container_org': 'docker_container_wizard_states_preliminary_organization',
    'cr_loc': 'compute_resource_location',
    'cr_org': 'compute_resource_organization',
    'discovery_rule_loc': 'discovery_rule_location',
    'discovery_rule_org': 'discovery_rule_organization',
    'env_org': 'environment_organization',
    'filter_org': 'filter_organization',
    'filter_loc': 'filter_location',
    'filter_permission': 'filter_permission',
    'loc_capsules': 'location_smart_proxy',
    'loc_domain': 'location_domain',
    'loc_envs': 'location_environment',
    'loc_hostgroup': 'location_hostgroup',
    'loc_media': 'location_medium',
    'loc_org': 'location_organization',
    'loc_ptable': 'location_ptable',
    'loc_resource': 'location_compute_resource',
    'loc_subnet': 'location_subnet',
    'loc_template': 'location_provisioning_template',
    'loc_user': 'location_user',
    'location_user': 'location_user',
    'org_capsules': 'organization_smart_proxy',
    'org_domain': 'organization_domain',
    'org_envs': 'organization_environment',
    'org_hostgroup': 'organization_hostgroup',
    'org_location': 'organization_location',
    'org_media': 'organization_medium',
    'org_ptable': 'organization_ptable',
    'org_resource': 'organization_compute_resource',
    'org_subnet': 'organization_subnet',
    'org_template': 'organization_provisioning_template',
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
    'role_loc': 'role_location',
    'role_org': 'role_organization',
    'sub_domain': 'subnet_domain',
    'subnet_org': 'subnet_organization',
    'template_os': 'provisioning_template_operatingsystem',
    'template_location': 'provisioning_template_location',
    'template_org': 'provisioning_template_organization',
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
SRPM_TO_UPLOAD = "which-2.19-6.el6.x86_64.src.rpm"

ENVIRONMENT = "Library"

NOT_IMPLEMENTED = 'Test not implemented'

SYNC_INTERVAL = {
    'hour': "hourly",
    'day': "daily",
    'week': "weekly"
}

REPO_TYPE = {
    'yum': "yum",
    'puppet': "puppet",
    'docker': "docker",
    'ostree': "ostree",
}

DOWNLOAD_POLICIES = {
    'on_demand': "On Demand",
    'background': "Background",
    'immediate': "Immediate"
}

CHECKSUM_TYPE = {
    'default': "Default",
    'sha256': "sha256",
    'sha1': "sha1",
}

REPO_TAB = {
    'rpms': "RPMs",
    'kickstarts': "Kickstarts",
    'isos': "ISOs",
    'ostree': "OSTree",
}

# On importing manifests, Red Hat repositories are listed like this:
# Product -> RepositorySet -> Repository
# We need to first select the Product, then the reposet and then the repos
# Example: 'rhel' is the name of Product that contains following REPOSETs
PRDS = {
    'rhcf': 'Red Hat CloudForms',
    'rhel': 'Red Hat Enterprise Linux Server',
    'rhah': 'Red Hat Enterprise Linux Atomic Host',
}

REPOSET = {
    'rhct6': 'Red Hat CloudForms Tools for RHEL 6 (RPMs)',
    'rhel6': 'Red Hat Enterprise Linux 6 Server (RPMs)',
    'rhva6': (
        'Red Hat Enterprise Virtualization Agents for RHEL 6 Server (RPMs)'
    ),
    'rhst7': 'Red Hat Satellite Tools 6.2 (for RHEL 7 Server) (RPMs)',
    'rhst6': 'Red Hat Satellite Tools 6.2 (for RHEL 6 Server) (RPMs)',
    'rhaht': 'Red Hat Enterprise Linux Atomic Host (Trees)'
}

REPOS = {
    'rhst7': {
        'id': 'rhel-7-server-satellite-tools-6.2-rpms',
        'name': (
            'Red Hat Satellite Tools 6.2 for RHEL 7 Server RPMs x86_64'
        ),
    },
    'rhst6': {
        'id': 'rhel-6-server-satellite-tools-6.2-rpms',
        'name': (
            'Red Hat Satellite Tools 6.2 for RHEL 6 Server RPMs x86_64'
        ),
    },
    'rhva6': {
        'id': 'rhel-6-server-rhev-agent-rpms',
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
    'rhaht': {
        'name': ('Red Hat Enterprise Linux Atomic Host Trees'),
    }
}

RHEL_6_MAJOR_VERSION = 6
RHEL_7_MAJOR_VERSION = 7

# The 'create_repos_tree' function under 'sync' module uses the following
# list of tuples. It actually includes following two repos under
# Reposet: Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs
#
# Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs x86_64 6.5
# Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs x86_64
# 6Server

RHVA_REPO_TREE = [
    (
        'rhel', 'rhva6', 'rhva65', 'repo_name',
        'Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs '
        'x86_64 6.5'
    ),
    ('rhel', 'rhva6', 'rhva65', 'repo_arch', 'x86_64'),
    ('rhel', 'rhva6', 'rhva65', 'repo_ver', '6.5'),
    (
        'rhel', 'rhva6', 'rhva6S', 'repo_name',
        'Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs '
        'x86_64 6Server'
    ),
    ('rhel', 'rhva6', 'rhva6S', 'repo_arch', 'x86_64'),
    ('rhel', 'rhva6', 'rhva6S', 'repo_ver', '6Server')
]

SAT6_TOOLS_TREE = [
    (
        'rhel', 'rhst6', 'rhst6', 'repo_name',
        'Red Hat Satellite Tools 6.2 for RHEL 6 Server RPMs x86_64'
    ),
    ('rhel', 'rhst6', 'rhst6', 'repo_arch', 'x86_64'),
    ('rhel', 'rhst6', 'rhst6', 'repo_ver', '6.2'),
]

ATOMIC_HOST_TREE = [
    (
        'rhah', 'rhaht', 'rhaht', 'repo_name',
        'Red Hat Enterprise Linux Atomic Host Trees'
    ),
    ('rhah', 'rhaht', 'rhaht', 'repo_arch', None),
    ('rhah', 'rhaht', 'rhaht', 'repo_ver', None),
]

DEFAULT_ORG_ID = 1
#: Name (not label!) of the default organization.
DEFAULT_ORG = "Default Organization"
#: Name (not label!) of the default location.
DEFAULT_LOC = "Default Location"
DEFAULT_CV = "Default Organization View"
DEFAULT_TEMPLATE = "Satellite Kickstart Default"
DEFAULT_PXE_TEMPLATE = "Kickstart default PXELinux"
DEFAULT_PTABLE = "Kickstart default"
DEFAULT_SUBSCRIPTION_NAME = (
    'Red Hat Enterprise Linux Server, Premium (Physical or Virtual Nodes)')
DEFAULT_ARCHITECTURE = 'x86_64'
DEFAULT_RELEASE_VERSION = '6Server'
DEFAULT_ROLE = 'Default role'

LANGUAGES = {
    u'Català': u'ca',
    u'Deutsch': u'de',
    u'English (United States)': u'en',
    u'English (United Kingdom)': u'en_GB',
    u'Español': u'es',
    u'Français': u'fr',
    u'Galego': u'gl',
    u'it': u'it',
    u'日本語': u'ja',
    u'한국어': u'ko',
    u'pl': u'pl',
    u'Português (Brasil)': u'pt_BR',
    u'Русский': u'ru',
    u'sv_SE': u'sv_SE',
    u'简体中文': u'zh_CN',
    u'zh_TW': u'zh_TW'
}

TIMEZONES = [
    u'(GMT+00:00) UTC',
    u'(GMT-10:00) Hawaii',
    u'(GMT+02:00) Kyiv',
    u'(GMT+08:00) Hong Kong',
    u'(GMT-07:00) Arizona',
]

FILTER_CONTENT_TYPE = {
    'package': "Package",
    'package group': "Package Group",
    'erratum by id': "Erratum - by ID",
    'erratum by date and type': "Erratum - by Date and Type"
}

FILTER_TYPE = {
    'include': "Include",
    'exclude': "Exclude"
}

FILTER_ERRATA_TYPE = {
    'security': "security",
    'enhancement': "enhancement",
    'bugfix': "bugfix"
}

FILTER_ERRATA_DATE = {
    'updated': "updated",
    'issued': "issued"
}

DOCKER_REGISTRY_HUB = u'https://registry-1.docker.io'
DOCKER_UPSTREAM_NAME = u'busybox'
CUSTOM_RPM_REPO = (
    u'http://repos.fedorapeople.org/repos/pulp/pulp/fixtures/rpm/'
)
FAKE_0_YUM_REPO = u'http://inecas.fedorapeople.org/fakerepos/zoo/'
FAKE_1_YUM_REPO = u'http://inecas.fedorapeople.org/fakerepos/zoo3/'
FAKE_2_YUM_REPO = u'http://inecas.fedorapeople.org/fakerepos/zoo2/'
FAKE_3_YUM_REPO = u'http://omaciel.fedorapeople.org/fakerepo01'
FAKE_4_YUM_REPO = u'http://omaciel.fedorapeople.org/fakerepo02'
FAKE_5_YUM_REPO = u'http://{0}:{1}@rplevka.fedorapeople.org/fakerepo01/'
FAKE_6_YUM_REPO = (
    u'https://jlsherrill.fedorapeople.org/fake-repos/needed-errata/'
)
FAKE_YUM_DRPM_REPO = (
    u'https://repos.fedorapeople.org/repos/pulp/pulp/fixtures/drpm/'
)
FAKE_YUM_SRPM_REPO = (
    u'https://repos.fedorapeople.org/repos/pulp/pulp/fixtures/srpm/'
)
CUSTOM_PUPPET_REPO = u'http://omaciel.fedorapeople.org/bagoftricks'
FAKE_0_PUPPET_REPO = u'http://davidd.fedorapeople.org/repos/random_puppet/'
FAKE_1_PUPPET_REPO = u'http://omaciel.fedorapeople.org/fakepuppet01'
FAKE_2_PUPPET_REPO = u'http://omaciel.fedorapeople.org/fakepuppet02'
FAKE_3_PUPPET_REPO = u'http://omaciel.fedorapeople.org/fakepuppet03'
FAKE_4_PUPPET_REPO = u'http://omaciel.fedorapeople.org/fakepuppet04'
FAKE_5_PUPPET_REPO = u'http://omaciel.fedorapeople.org/fakepuppet05'
FAKE_6_PUPPET_REPO = u'http://kbidarka.fedorapeople.org/repos/puppet-modules/'
FAKE_7_PUPPET_REPO = u'http://{0}:{1}@rplevka.fedorapeople.org/fakepuppet01/'
FEDORA22_OSTREE_REPO = u'https://kojipkgs.fedoraproject.org/atomic/22/'
FEDORA23_OSTREE_REPO = u'https://kojipkgs.fedoraproject.org/atomic/23/'
REPO_DISCOVERY_URL = u'http://omaciel.fedorapeople.org/'
FAKE_0_CUSTOM_PACKAGE = 'bear-4.1-1.noarch'
FAKE_0_CUSTOM_PACKAGE_NAME = 'bear'
FAKE_1_CUSTOM_PACKAGE = 'walrus-0.71-1.noarch'
FAKE_1_CUSTOM_PACKAGE_NAME = 'walrus'
FAKE_2_CUSTOM_PACKAGE = 'walrus-5.21-1.noarch'
FAKE_2_CUSTOM_PACKAGE_NAME = 'walrus'
REAL_0_RH_PACKAGE = 'rhevm-sdk-python-3.3.0.21-1.el6ev.noarch'
FAKE_0_CUSTOM_PACKAGE_GROUP_NAME = 'birds'
FAKE_0_ERRATA_ID = 'RHEA-2012:0001'
FAKE_1_ERRATA_ID = 'RHEA-2012:0002'
FAKE_2_ERRATA_ID = 'RHEA-2012:0055'  # for FAKE_6_YUM_REPO
FAKE_3_ERRATA_ID = 'RHEA-2012:7269'  # for FAKE_3_YUM_REPO
REAL_0_ERRATA_ID = 'RHBA-2016:1503'  # for rhst7
REAL_1_ERRATA_ID = 'RHBA-2016:1357'  # for REAL_0_RH_PACKAGE
REAL_2_ERRATA_ID = 'RHEA-2014:0657'  # for REAL_0_RH_PACKAGE
REAL_4_ERRATA_ID = 'RHSA-2014:1873'  # for rhst6 with type=security and cves
REAL_4_ERRATA_CVES = ['CVE-2014-3633', 'CVE-2014-3657', 'CVE-2014-7823']
FAKE_0_YUM_ERRATUM_COUNT = 4
FAKE_1_YUM_ERRATUM_COUNT = 4
FAKE_3_YUM_ERRATUM_COUNT = 79
FAKE_6_YUM_ERRATUM_COUNT = 4

PUPPET_MODULE_NTP_PUPPETLABS = "puppetlabs-ntp-3.2.1.tar.gz"

FAKE_0_CUSTOM_PACKAGE_GROUP = [
    'cockateel-3.1-1.noarch',
    'duck-0.6-1.noarch',
    'penguin-0.9.1-1.noarch',
    'stork-0.12-2.noarch',
]

FAKE_0_PUPPET_MODULE = 'httpd'

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
        'create_arf_reports',
        'create_containers',
        'create_recurring_logics',
        'create_registries',
        'destroy_arf_reports',
        'destroy_config_reports',
        'destroy_containers',
        'destroy_registries',
        'download_bootdisk',
        'edit_recurring_logics',
        'logs',
        'my_organizations',
        'rh_telemetry_api',
        'rh_telemetry_configurations',
        'rh_telemetry_view',
        'search_repository_image_search',
        'upload_config_reports',
        'view_arf_reports',
        'view_cases',
        'view_config_reports',
        'view_containers',
        'view_log_viewer',
        'view_plugins',
        'view_recurring_logics',
        'view_registries',
        'view_search',
        'view_statistics',
        'view_tasks',
    ],
    'AnsibleRole': [
        'destroy_ansible_roles',
        'import_ansible_roles',
        'view_ansible_roles',
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
    'ForemanTasks::RecurringLogic': [
        'create_recurring_logics',
        'view_recurring_logics',
        'edit_recurring_logics',
    ],
    'ForemanOpenscap::Policy': [
        'assign_policies',
        'create_policies',
        'destroy_policies',
        'edit_policies',
        'view_policies',
    ],
    'ForemanOpenscap::ScapContent': [
        'create_scap_contents',
        'destroy_scap_contents',
        'edit_scap_contents',
        'view_scap_contents',
    ],
    'ForemanTasks::Task': [
        u'edit_foreman_tasks',
        u'view_foreman_tasks',
    ],
    'JobInvocation': [
        'view_job_invocations',
        'create_job_invocations',
    ],
    'JobTemplate': [
        'view_job_templates',
        'edit_job_templates',
        'destroy_job_templates',
        'create_job_templates',
        'lock_job_templates',
    ],
    'CommonParameter': [
        'view_globals',
        'create_globals',
        'edit_globals',
        'destroy_globals',
    ],
    'ConfigReport': [
        'destroy_config_reports',
        'view_config_reports',
        'upload_config_reports',
    ],
    'HostClass': [
        'edit_classes',
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
    'Parameter': [
        'view_params',
        'create_params',
        'edit_params',
        'destroy_params',
    ],
    'ProvisioningTemplate': [
        'view_provisioning_templates',
        'create_provisioning_templates',
        'edit_provisioning_templates',
        'destroy_provisioning_templates',
        'deploy_provisioning_templates',
        'lock_provisioning_templates',
    ],
    'Ptable': [
        'view_ptables',
        'create_ptables',
        'edit_ptables',
        'destroy_ptables',
        'lock_ptables',
    ],
    'Puppetclass': [
        'view_puppetclasses',
        'create_puppetclasses',
        'edit_puppetclasses',
        'destroy_puppetclasses',
        'import_puppetclasses',
    ],
    'PuppetclassLookupKey': [
        'view_external_parameters',
        'create_external_parameters',
        'edit_external_parameters',
        'destroy_external_parameters',
    ],
    'Realm': [
        'view_realms',
        'create_realms',
        'edit_realms',
        'destroy_realms',
    ],
    'RemoteExecutionFeature': [
        'edit_remote_execution_features',
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
        'view_capsule_content'
    ],
    'Subnet': [
        'view_subnets',
        'create_subnets',
        'edit_subnets',
        'destroy_subnets',
        'import_subnets',
    ],
    'TemplateInvocation': [
        'filter_autocompletion_for_template_invocation',
        'execute_template_invocation',
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
    'VariableLookupKey': [
        'view_external_variables',
        'create_external_variables',
        'edit_external_variables',
        'destroy_external_variables',
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
        'play_roles',
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
    'Katello::ContentView': [
        'view_content_views',
        'create_content_views',
        'edit_content_views',
        'destroy_content_views',
        'publish_content_views',
        'promote_or_remove_content_views',
        'export_content_views',
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
        'export_products',
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

ANY_CONTEXT = {
    'org': "Any Organization",
    'location': "Any Location"
}

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
    'esp': 'Example Server Profile',
    'rhccp': ('Red Hat Corporate Profile for '
              'Certified Cloud Providers (RH CCP)'),
    'usgcb': 'United States Government Configuration Baseline (USGCB)',
    'common': 'Common Profile for General-Purpose Systems',
}

ROLES = [
    'Access Insights Admin',
    'Access Insights Viewer',
    'Boot disk access',
    'Compliance manager',
    'Compliance viewer',
    'Discovery Manager',
    'Discovery Reader',
    'Edit hosts',
    'Edit partition tables',
    'Red Hat Access Logs',
    'Remote Execution Manager',
    'Remote Execution User',
    'Site manager',
    'Tasks Manager',
    'Tasks Reader',
    'View hosts',
    'Manager',
    'Viewer',
]

BOOKMARK_ENTITIES = [
    {'name': 'ActivationKey', 'controller': 'katello_activation_keys'},
    {'name': 'Dashboard', 'controller': 'dashboard', 'skip_for_ui': True},
    {'name': 'Fact', 'controller': 'fact_values', 'skip_for_ui': True},
    {'name': 'Audit', 'controller': 'audits', 'skip_for_ui': True},
    {'name': 'Report', 'controller': 'config_reports', 'skip_for_ui': True},
    {'name': 'Task', 'controller': 'foreman_tasks_tasks', 'skip_for_ui': True},
    {'name': 'Subscriptions', 'controller': 'katello_subscriptions'},
    {'name': 'Products', 'controller': 'katello_products'},
    {
        'name': 'Repository', 'controller': 'katello_repositories',
        'skip_for_ui': True
    },
    {'name': 'GPGKey', 'controller': 'katello_gpg_keys'},
    {'name': 'SyncPlan', 'controller': 'katello_sync_plans'},
    {'name': 'Content_Views', 'controller': 'katello_content_views'},
    {'name': 'Errata', 'controller': 'katello_errata', 'skip_for_ui': True},
    {
        'name': 'Package', 'controller': 'katello_erratum_packages',
        'skip_for_ui': True
    },
    {
        'name': 'PuppetModule', 'controller': 'katello_puppet_modules',
        'skip_for_ui': True
    },
    {
        'name': 'DockerTag', 'controller': 'katello_docker_tags',
        'skip_for_ui': True
    },
    {
        'name': 'Registry', 'controller': 'docker_registries',
        'skip_for_ui': 1302724
    },
    {'name': 'Hosts', 'controller': 'hosts', 'setup': entities.Host},
    {
        'name': 'ContentHost', 'controller': 'hosts',
        'skip_for_ui': True
    },
    {'name': 'HostCollection', 'controller': 'katello_host_collections'},
    {'name': 'Architecture', 'controller': 'architectures'},
    {'name': 'HardwareModel', 'controller': 'models', 'setup': entities.Model},
    {
        'name': 'InstallationMedia', 'controller': 'media',
        'setup': entities.Media, 'skip_for_ui': True
    },
    {'name': 'OperatingSys', 'controller': 'operatingsystems'},
    {
        'name': 'PartitionTable', 'controller': 'ptables',
        'setup': entities.PartitionTable, 'skip_for_ui': False
    },
    {'name': 'Template', 'controller': 'provisioning_templates'},
    {
        'name': 'HostGroup', 'controller': 'hostgroups',
        'setup': entities.HostGroup
    },
    {
        'name': 'DiscoveryRules', 'controller': 'discovery_rules',
        'skip_for_ui': 1387569, 'setup': entities.DiscoveryRule
    },
    {
        'name': 'GlobalParameter', 'controller': 'common_parameters',
        'setup': entities.CommonParameter, 'skip_for_ui': True
    },
    {
        'name': 'ConfigGroups', 'controller': 'config_groups',
        'setup': entities.ConfigGroup, 'skip_for_ui': 1378084
    },
    {
        'name': 'PuppetEnv', 'controller': 'environments',
        'setup': entities.Environment, 'skip_for_ui': True
    },
    {
        'name': 'PuppetClasses', 'controller': 'puppetclasses',
        'setup': entities.PuppetClass
    },
    {
        'name': 'SmartVariable', 'controller': 'lookup_keys',
        'setup': entities.SmartVariable, 'skip_for_ui': True
    },
    {'name': 'SmartProxy', 'controller': 'smart_proxies', 'skip_for_ui': True},
    {
        'name': 'Compute_Resource', 'controller': 'compute_resources',
        'setup': entities.DockerComputeResource
    },
    {
        'name': 'Compute_Profile', 'controller': 'compute_profiles',
        'setup': entities.ComputeProfile
    },
    {
        'name': 'Subnet', 'controller': 'subnets',
        'setup': entities.Subnet
    },
    {'name': 'Domain', 'controller': 'domains', 'setup': entities.Domain},
    {
        'name': 'Realm', 'controller': 'realms', 'setup': entities.Realm,
        'skip_for_ui': True
    },
    {'name': 'Location', 'controller': 'locations'},
    {'name': 'Org', 'controller': 'organizations'},
    {'name': 'User', 'controller': 'users'},
    {
        'name': 'UserGroup', 'controller': 'usergroups',
        'setup': entities.UserGroup
    },
    {'name': 'Role', 'controller': 'roles'},
    {'name': 'Settings', 'controller': 'settings'},
]

STRING_TYPES = [
    u'alpha', u'numeric', u'alphanumeric',
    u'latin1', u'utf8', u'cjk', u'html'
]

# All UI crud classes listed here to allow dynamical import
# import import_string; import_string('robottelo.ui.{0}'.format(item))
UI_CRUD = [
    'activationkey.ActivationKey',
    'architecture.Architecture',
    'bookmark.Bookmark',
    'computeprofile.ComputeProfile',
    'computeresource.ComputeResource',
    'configgroups.ConfigGroups',
    'container.Container',
    'contenthost.ContentHost',
    'contentviews.ContentViews',
    'discoveredhosts.DiscoveredHosts',
    'discoveryrules.DiscoveryRules',
    'dockertag.DockerTag',
    'domain.Domain',
    'environment.Environment',
    'errata.Errata',
    'gpgkey.GPGKey',
    'hardwaremodel.HardwareModel',
    'hostcollection.HostCollection',
    'hostgroup.Hostgroup',
    'hosts.Hosts',
    'job.Job',
    'job_template.JobTemplate',
    'ldapauthsource.LdapAuthSource',
    'lifecycleenvironment.LifecycleEnvironment',
    'location.Location',
    'login.Login',
    'medium.Medium',
    'navigator.Navigator',
    'operatingsys.OperatingSys',
    'org.Org',
    'oscapcontent.OpenScapContent',
    'oscappolicy.OpenScapPolicy',
    'oscapreports.OpenScapReports',
    'packages.Package',
    'partitiontable.PartitionTable',
    'products.Products',
    'puppetclasses.PuppetClasses',
    'registry.Registry',
    'repository.Repos',
    'rhai.RHAI',
    'role.Role',
    'settings.Settings',
    'subnet.Subnet',
    'subscription.Subscriptions',
    'sync.Sync',
    'syncplan.Syncplan',
    'systemgroup.SystemGroup',
    'template.Template',
    'trend.Trend',
    'usergroup.UserGroup',
    'user.User'
]

BACKUP_FILES = [
    u'candlepin.dump',
    u'config_files.tar.gz',
    u'config.snar',
    u'foreman.dump',
    u'mongo_dump',
    u'pulp_data.tar',
    u'pulp.snar',
]

TOOLS_ERRATA_DETAILS = [
    ['Advisory', 'RHBA-2016:1503'],
    ['CVEs', 'N/A'],
    ['Type', 'Bug Fix Advisory'],
    ['Severity', 'None'],
    ['Issued', '7/27/16'],
    ['Last Updated On', '7/27/16'],
    ['Reboot Suggested', 'No'],
    [
        'Topic',
        'Red Hat Satellite 6.2 now available for Red Hat Enterprise Linux 6 '
        'and 7'
    ],
    ['Description', 'This update provides Satellite 6.2 client tooling'],
    [
        'Solution',
        'Before applying this update, make sure all previously released errata'
    ],
]

TOOLS_ERRATA_TABLE_DETAILS = [
    'RHBA-2016:1503',
    'Satellite 6.2 Tools Release',
    'Bug Fix Advisory',
    'Installable',
    '7/27/16'
]

# To create custom role for bugzilla's
# Append bugzilla id to dict, also see utils.get_perms_by_bz()
PERMISSIONS_WITH_BZ = {
    None: [
        {'name': 'access_dashboard', 'bz': [1306359]},
        {'name': 'access_settings', 'bz': [1306359]},
        {'name': 'app_root'},
        {'name': 'attachments'},
        {'name': 'commit_containers'},
        {'name': 'configuration'},
        {'name': 'create_arf_reports'},
        {'name': 'create_containers'},
        {'name': 'create_recurring_logics'},
        {'name': 'create_registries'},
        {'name': 'destroy_arf_reports'},
        {'name': 'destroy_config_reports'},
        {'name': 'destroy_containers'},
        {'name': 'destroy_registries'},
        {'name': 'download_bootdisk'},
        {'name': 'edit_recurring_logics'},
        {'name': 'logs'},
        {'name': 'my_organizations', 'bz': [1306359]},
        {'name': 'rh_telemetry_api'},
        {'name': 'rh_telemetry_configurations'},
        {'name': 'rh_telemetry_view'},
        {'name': 'search_repository_image_search'},
        {'name': 'upload_config_reports'},
        {'name': 'view_arf_reports'},
        {'name': 'view_cases', 'bz': [1306359]},
        {'name': 'view_config_reports'},
        {'name': 'view_containers'},
        {'name': 'view_log_viewer', 'bz': [1306359]},
        {'name': 'view_plugins', 'bz': [1306359]},
        {'name': 'view_recurring_logics'},
        {'name': 'view_registries'},
        {'name': 'view_search', 'bz': [1306359]},
        {'name': 'view_statistics', 'bz': [1306359]},
        {'name': 'view_tasks', 'bz': [1306359]},
    ],
    'AnsibleRole': [
        {'name': 'destroy_ansible_roles'},
        {'name': 'import_ansible_roles'},
        {'name': 'view_ansible_roles'},
    ],
    'Architecture': [
        {'name': 'view_architectures', 'bz': [1306359]},
        {'name': 'create_architectures'},
        {'name': 'edit_architectures'},
        {'name': 'destroy_architectures'},
    ],
    'Audit': [
        {'name': 'view_audit_logs', 'bz': [1306359]},
    ],
    'AuthSourceLdap': [
        {'name': 'view_authenticators', 'bz': [1306359]},
        {'name': 'create_authenticators'},
        {'name': 'edit_authenticators'},
        {'name': 'destroy_authenticators'},
    ],
    'Bookmark': [
        {'name': 'view_bookmarks'},
        {'name': 'create_bookmarks'},
        {'name': 'edit_bookmarks'},
        {'name': 'destroy_bookmarks'},
    ],
    'ConfigGroup': [
        {'name': 'view_config_groups'},
        {'name': 'create_config_groups'},
        {'name': 'edit_config_groups'},
        {'name': 'destroy_config_groups'},
    ],
    'Container': [
        {'name': 'commit_containers'},
        {'name': 'create_containers'},
        {'name': 'destroy_containers'},
        {'name': 'view_containers'},
    ],
    'ComputeProfile': [
        {'name': 'view_compute_profiles'},
        {'name': 'create_compute_profiles'},
        {'name': 'edit_compute_profiles'},
        {'name': 'destroy_compute_profiles'},
    ],
    'ComputeResource': [
        {'name': 'view_compute_resources'},
        {'name': 'create_compute_resources'},
        {'name': 'edit_compute_resources'},
        {'name': 'destroy_compute_resources'},
        {'name': 'view_compute_resources_vms'},
        {'name': 'create_compute_resources_vms'},
        {'name': 'edit_compute_resources_vms'},
        {'name': 'destroy_compute_resources_vms'},
        {'name': 'power_compute_resources_vms'},
        {'name': 'console_compute_resources_vms'},
    ],
    'DiscoveryRule': [
        {'name': 'create_discovery_rules'},
        {'name': 'destroy_discovery_rules'},
        {'name': 'edit_discovery_rules'},
        {'name': 'execute_discovery_rules'},
        {'name': 'view_discovery_rules'},
    ],
    'Docker/ImageSearch': [
        {'name': 'search_repository_image_search'},
    ],
    'DockerRegistry': [
        {'name': 'create_registries'},
        {'name': 'destroy_registries'},
        {'name': 'view_registries'},
    ],
    'Domain': [
        {'name': 'view_domains', 'bz': [1306359]},
        {'name': 'create_domains', 'bz': [1306359]},
        {'name': 'edit_domains', 'bz': [1306359]},
        {'name': 'destroy_domains', 'bz': [1306359]},
    ],
    'Environment': [
        {'name': 'view_environments', 'bz': [1306359]},
        {'name': 'create_environments', 'bz': [1306359]},
        {'name': 'edit_environments', 'bz': [1306359]},
        {'name': 'destroy_environments', 'bz': [1306359]},
        {'name': 'import_environments', 'bz': [1306359]},
    ],
    'ExternalUsergroups': [
        {'name': 'view_external_usergroups'},
        {'name': 'create_external_usergroups'},
        {'name': 'edit_external_usergroups'},
        {'name': 'destroy_external_usergroups'},
    ],
    'FactValue': [
        {'name': 'view_facts', 'bz': [1306359]},
        {'name': 'upload_facts'},
    ],
    'Filter': [
        {'name': 'view_filters', 'bz': [1306359]},
        {'name': 'create_filters', 'bz': [1306359]},
        {'name': 'edit_filters', 'bz': [1306359]},
        {'name': 'destroy_filters', 'bz': [1306359]},
    ],
    'ForemanTasks::RecurringLogic': [
        {'name': 'create_recurring_logics'},
        {'name': 'view_recurring_logics'},
        {'name': 'edit_recurring_logics'},
    ],
    'ForemanOpenscap::Policy': [
        {'name': 'assign_policies'},
        {'name': 'create_policies'},
        {'name': 'destroy_policies'},
        {'name': 'edit_policies'},
        {'name': 'view_policies'},
    ],
    'ForemanOpenscap::ScapContent': [
        {'name': 'create_scap_contents'},
        {'name': 'destroy_scap_contents'},
        {'name': 'edit_scap_contents'},
        {'name': 'view_scap_contents'},
    ],
    'ForemanTasks::Task': [
        {'name': u'edit_foreman_tasks'},
        {'name': u'view_foreman_tasks'},
    ],
    'JobInvocation': [
        {'name': 'view_job_invocations'},
        {'name': 'create_job_invocations'},
    ],
    'JobTemplate': [
        {'name': 'view_job_templates'},
        {'name': 'edit_job_templates'},
        {'name': 'destroy_job_templates'},
        {'name': 'create_job_templates'},
        {'name': 'lock_job_templates'},
    ],
    'CommonParameter': [
        {'name': 'view_globals', 'bz': [1306359]},
        {'name': 'create_globals'},
        {'name': 'edit_globals'},
        {'name': 'destroy_globals'},
    ],
    'ConfigReport': [
        {'name': 'destroy_config_reports'},
        {'name': 'view_config_reports'},
        {'name': 'upload_config_reports'},
    ],
    'HostClass': [
        {'name': 'edit_classes'},
    ],
    'Hostgroup': [
        {'name': 'view_hostgroups'},
        {'name': 'create_hostgroups'},
        {'name': 'edit_hostgroups'},
        {'name': 'destroy_hostgroups'},
    ],
    'Image': [
        {'name': 'view_images'},
        {'name': 'create_images'},
        {'name': 'edit_images'},
        {'name': 'destroy_images'},
    ],
    'Location': [
        {'name': 'view_locations'},
        {'name': 'create_locations'},
        {'name': 'edit_locations'},
        {'name': 'destroy_locations'},
        {'name': 'assign_locations'},
    ],
    'MailNotification': [
        {'name': 'view_mail_notifications'},
    ],
    'Medium': [
        {'name': 'view_media', 'bz': [1306359]},
        {'name': 'create_media', 'bz': [1306359]},
        {'name': 'edit_media', 'bz': [1306359]},
        {'name': 'destroy_media', 'bz': [1306359]},
    ],
    'Model': [
        {'name': 'view_models', 'bz': [1306359]},
        {'name': 'create_models'},
        {'name': 'edit_models'},
        {'name': 'destroy_models'},
    ],
    'Operatingsystem': [
        {'name': 'view_operatingsystems', 'bz': [1306359]},
        {'name': 'create_operatingsystems', 'bz': [1306359]},
        {'name': 'edit_operatingsystems', 'bz': [1306359]},
        {'name': 'destroy_operatingsystems'},
    ],
    'Parameter': [
        {'name': 'view_params'},
        {'name': 'create_params'},
        {'name': 'edit_params'},
        {'name': 'destroy_params'},
    ],
    'ProvisioningTemplate': [
        {'name': 'view_provisioning_templates'},
        {'name': 'create_provisioning_templates'},
        {'name': 'edit_provisioning_templates'},
        {'name': 'destroy_provisioning_templates'},
        {'name': 'deploy_provisioning_templates'},
        {'name': 'lock_provisioning_templates'},
    ],
    'Ptable': [
        {'name': 'view_ptables', 'bz': [1306359]},
        {'name': 'create_ptables', 'bz': [1306359]},
        {'name': 'edit_ptables', 'bz': [1306359]},
        {'name': 'destroy_ptables', 'bz': [1306359]},
        {'name': 'lock_ptables'},
    ],
    'Puppetclass': [
        {'name': 'view_puppetclasses', 'bz': [1306359]},
        {'name': 'create_puppetclasses', 'bz': [1306359]},
        {'name': 'edit_puppetclasses', 'bz': [1306359]},
        {'name': 'destroy_puppetclasses', 'bz': [1306359]},
        {'name': 'import_puppetclasses', 'bz': [1306359]},
    ],
    'PuppetclassLookupKey': [
        {'name': 'view_external_parameters'},
        {'name': 'create_external_parameters'},
        {'name': 'edit_external_parameters'},
        {'name': 'destroy_external_parameters'},
    ],
    'Realm': [
        {'name': 'view_realms', 'bz': [1306359]},
        {'name': 'create_realms', 'bz': [1306359]},
        {'name': 'edit_realms', 'bz': [1306359]},
        {'name': 'destroy_realms', 'bz': [1306359]},
    ],
    'RemoteExecutionFeature': [
        {'name': 'edit_remote_execution_features'},
    ],
    'Report': [
        {'name': 'view_reports', 'bz': [1306359]},
        {'name': 'destroy_reports'},
        {'name': 'upload_reports'},
    ],
    'Role': [
        {'name': 'view_roles'},
        {'name': 'create_roles'},
        {'name': 'edit_roles'},
        {'name': 'destroy_roles'},
    ],
    'SmartProxy': [
        {'name': 'view_smart_proxies', 'bz': [1306359]},
        {'name': 'create_smart_proxies'},
        {'name': 'edit_smart_proxies', 'bz': [1306359]},
        {'name': 'destroy_smart_proxies'},
        {'name': 'view_smart_proxies_autosign', 'bz': [1306359]},
        {'name': 'create_smart_proxies_autosign'},
        {'name': 'destroy_smart_proxies_autosign'},
        {'name': 'view_smart_proxies_puppetca', 'bz': [1306359]},
        {'name': 'edit_smart_proxies_puppetca'},
        {'name': 'destroy_smart_proxies_puppetca'},
        {'name': 'manage_capsule_content'},
        {'name': 'view_capsule_content'},
    ],
    'Subnet': [
        {'name': 'view_subnets', 'bz': [1306359]},
        {'name': 'create_subnets', 'bz': [1306359]},
        {'name': 'edit_subnets', 'bz': [1306359]},
        {'name': 'destroy_subnets', 'bz': [1306359]},
        {'name': 'import_subnets', 'bz': [1306359]},
    ],
    'TemplateInvocation': [
        {'name': 'filter_autocompletion_for_template_invocation'},
        {'name': 'execute_template_invocation'},
    ],
    'Trend': [
        {'name': 'view_trends'},
        {'name': 'create_trends'},
        {'name': 'edit_trends'},
        {'name': 'destroy_trends'},
        {'name': 'update_trends'},
    ],
    'Usergroup': [
        {'name': 'view_usergroups', 'bz': [1306359]},
        {'name': 'create_usergroups'},
        {'name': 'edit_usergroups'},
        {'name': 'destroy_usergroups'},
    ],
    'User': [
        {'name': 'view_users', 'bz': [1306359]},
        {'name': 'create_users'},
        {'name': 'edit_users'},
        {'name': 'destroy_users'},
    ],
    'VariableLookupKey': [
        {'name': 'view_external_variables', 'bz': [1306359]},
        {'name': 'create_external_variables', 'bz': [1306359]},
        {'name': 'edit_external_variables', 'bz': [1306359]},
        {'name': 'destroy_external_variables', 'bz': [1306359]},
    ],
    'Host': [
        {'name': 'auto_provision_discovered_hosts'},
        {'name': 'build_hosts'},
        {'name': 'console_hosts'},
        {'name': 'create_hosts'},
        {'name': 'destroy_discovered_hosts'},
        {'name': 'destroy_hosts'},
        {'name': 'edit_discovered_hosts'},
        {'name': 'edit_hosts'},
        {'name': 'ipmi_boot'},
        {'name': 'power_hosts'},
        {'name': 'provision_discovered_hosts'},
        {'name': 'puppetrun_hosts'},
        {'name': 'play_roles'},
        {'name': 'submit_discovered_hosts'},
        {'name': 'view_discovered_hosts'},
        {'name': 'view_hosts'},
    ],
    'Katello::ActivationKey': [
        {'name': 'view_activation_keys', 'bz': [1306359]},
        {'name': 'create_activation_keys', 'bz': [1306359]},
        {'name': 'edit_activation_keys', 'bz': [1306359]},
        {'name': 'destroy_activation_keys', 'bz': [1306359]},
    ],
    'Katello::ContentView': [
        {'name': 'view_content_views', 'bz': [1306359]},
        {'name': 'create_content_views', 'bz': [1306359]},
        {'name': 'edit_content_views', 'bz': [1306359]},
        {'name': 'destroy_content_views', 'bz': [1306359]},
        {'name': 'publish_content_views', 'bz': [1306359]},
        {'name': 'promote_or_remove_content_views', 'bz': [1306359]},
        {'name': 'export_content_views'},
    ],
    'Katello::GpgKey': [
        {'name': 'view_gpg_keys'},
        {'name': 'create_gpg_keys'},
        {'name': 'edit_gpg_keys'},
        {'name': 'destroy_gpg_keys'},
    ],
    'Katello::HostCollection': [
        {'name': 'view_host_collections', 'bz': [1306359]},
        {'name': 'create_host_collections', 'bz': [1306359]},
        {'name': 'edit_host_collections', 'bz': [1306359]},
        {'name': 'destroy_host_collections', 'bz': [1306359]},
    ],
    'Katello::KTEnvironment': [
        {'name': 'view_lifecycle_environments', 'bz': [1306359]},
        {'name': 'create_lifecycle_environments', 'bz': [1306359]},
        {'name': 'edit_lifecycle_environments', 'bz': [1306359]},
        {'name': 'destroy_lifecycle_environments', 'bz': [1306359]},
        {'name': 'promote_or_remove_content_views_to_environments',
            'bz': [1306359]},
    ],
    'Katello::Product': [
        {'name': 'view_products', 'bz': [1306359]},
        {'name': 'create_products'},
        {'name': 'edit_products', 'bz': [1306359]},
        {'name': 'destroy_products', 'bz': [1306359]},
        {'name': 'sync_products', 'bz': [1306359]},
        {'name': 'export_products'},
    ],
    'Organization': [
        {'name': 'view_organizations', 'bz': [1306359]},
        {'name': 'create_organizations'},
        {'name': 'edit_organizations'},
        {'name': 'destroy_organizations'},
        {'name': 'assign_organizations'},
        {'name': 'view_subscriptions', 'bz': [1306359]},
        {'name': 'attach_subscriptions', 'bz': [1306359]},
        {'name': 'unattach_subscriptions', 'bz': [1306359]},
        {'name': 'import_manifest', 'bz': [1306359]},
        {'name': 'delete_manifest', 'bz': [1306359]},
    ],
    'Katello::SyncPlan': [
        {'name': 'view_sync_plans', 'bz': [1306359]},
        {'name': 'create_sync_plans', 'bz': [1306359]},
        {'name': 'edit_sync_plans', 'bz': [1306359]},
        {'name': 'destroy_sync_plans', 'bz': [1306359]},
    ],
}
