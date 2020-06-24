# -*- encoding: utf-8 -*-
"""Defines various constants"""
from nailgun import entities

LOCALES = (
    'ca',
    'de',
    'en',
    'en_GB',
    'es',
    'fr',
    'gl',
    'it',
    'ja',
    'ko',
    'pt_BR',
    'ru',
    'sv_SE',
    'zh_CN',
    'zh_TW',
)

DISTRO_RHEL6 = "rhel6"
DISTRO_RHEL7 = "rhel7"
DISTRO_RHEL8 = "rhel8"
DISTRO_SLES11 = "sles11"
DISTRO_SLES12 = "sles12"

RHEL_6_MAJOR_VERSION = 6
RHEL_7_MAJOR_VERSION = 7
RHEL_8_MAJOR_VERSION = 8

DISTRO_DEFAULT = DISTRO_RHEL7
DISTROS_SUPPORTED = [DISTRO_RHEL6, DISTRO_RHEL7, DISTRO_RHEL8]
DISTROS_MAJOR_VERSION = {
    DISTRO_RHEL6: RHEL_6_MAJOR_VERSION,
    DISTRO_RHEL7: RHEL_7_MAJOR_VERSION,
    DISTRO_RHEL8: RHEL_8_MAJOR_VERSION,
}
MAJOR_VERSION_DISTRO = {value: key for key, value in DISTROS_MAJOR_VERSION.items()}


INTERFACE_API = 'API'
INTERFACE_CLI = 'CLI'

FOREMAN_PROVIDERS = {
    'libvirt': 'Libvirt',
    'rhev': 'RHV',
    'ec2': 'EC2',
    'vmware': 'VMware',
    'openstack': 'RHEL OpenStack Platform',
    'rackspace': 'Rackspace',
    'google': 'Google',
    'azurerm': 'Azure Resource Manager',
}

EC2_REGION_CA_CENTRAL_1 = 'ca-central-1'

CONTENT_CREDENTIALS_TYPES = {'gpg': 'GPG Key', 'ssl': 'SSL Certificate'}

VIRT_WHO_HYPERVISOR_TYPES = {
    'esx': 'esx',
    'hyperv': 'hyperv',
    'libvirt': 'libvirt',
    'rhevm': 'rhevm',
    'xen': 'xen',
}

LIBVIRT_RESOURCE_URL = 'qemu+ssh://root@%s/system'

RHEV_CR = '%s (RHV)'

AWS_EC2_FLAVOR_T2_MICRO = 't2.micro - Micro Instance'

COMPUTE_PROFILE_LARGE = '3-Large'
COMPUTE_PROFILE_SMALL = '1-Small'

# GCE specific constants
_bcds = dict.fromkeys(['us-east1', 'europe-west1'], ['b', 'c', 'd'])
_abcfs = dict.fromkeys(['us-central1'], ['a', 'b', 'c', 'f'])
_abcs = dict.fromkeys(
    [
        'us-east4',
        'us-west1',
        'europe-west4',
        'europe-west3',
        'europe-west2',
        'asia-east1',
        'asia-southeast1',
        'asia-northeast1',
        'asia-south1',
        'australia-southeast1',
        'southamerica-east1',
        'asia-east2',
        'asia-northeast2',
        'europe-north1',
        'europe-west6',
        'northamerica-northeast1',
        'us-west2',
    ],
    ['a', 'b', 'c'],
)
_zones_combo = {**_bcds, **_abcfs, **_abcs}
VALID_GCE_ZONES = [f'{loc}-{zone}' for loc, zones in _zones_combo.items() for zone in zones]
LATEST_RHEL7_GCE_IMG_UUID = '7726764279310511390'

GCE_MACHINE_TYPE_DEFAULT = 'f1-micro'
GCE_NETWORK_DEFAULT = 'default'
GCE_EXTERNAL_IP_DEFAULT = True

# AzureRM specific constants
AZURERM_VALID_REGIONS = [
    'East Asia',
    'Southeast Asia',
    'Central US',
    'East US',
    'East US 2',
    'West US',
    'North Central US',
    'South Central US',
    'North Europe',
    'West Europe',
    'Japan West',
    'Japan East',
    'Brazil South',
    'Australia East',
    'Australia Southeast',
    'South India',
    'Central India',
    'West India',
    'Canada Central',
    'Canada East',
    'UK South',
    'UK West',
    'West Central US',
    'West US 2',
    'Korea Central',
    'Korea South',
    'France Central',
    'France South',
    'Australia Central',
    'Australia Central 2',
    'UAE Central',
    'UAE North',
    'South Africa North',
    'South Africa West',
    'Switzerland North',
    'Switzerland West',
    'Germany North',
    'Germany West Central',
    'Norway West',
    'Norway East',
]
AZURERM_RHEL7_FT_IMG_URN = 'RedHat:RHEL:7-RAW:latest'
AZURERM_RHEL7_UD_IMG_URN = 'RedHat:RHEL:7-RAW-CI:7.6.2019072418'
AZURERM_RG_DEFAULT = 'SATQE'
AZURERM_PLATFORM_DEFAULT = 'Linux'
AZURERM_VM_SIZE_DEFAULT = 'Standard_B2ms'
AZURERM_PREMIUM_OS_Disk = True
AZURERM_FILE_URI = 'https://github.com/SatelliteQE/robottelo/blob/master/tests/foreman/data/uri.sh'

HTML_TAGS = [
    'A',
    'ABBR',
    'ACRONYM',
    'ADDRESS',
    'APPLET',
    'AREA',
    'B',
    'BASE',
    'BASEFONT',
    'BDO',
    'BIG',
    'BLINK',
    'BLOCKQUOTE',
    'BODY',
    'BR',
    'BUTTON',
    'CAPTION',
    'CENTER',
    'CITE',
    'CODE',
    'COL',
    'COLGROUP',
    'DD',
    'DEL',
    'DFN',
    'DIR',
    'DIV',
    'DL',
    'DT',
    'EM',
    'FIELDSET',
    'FONT',
    'FORM',
    'FRAME',
    'FRAMESET',
    'H1',
    'H2',
    'H3',
    'H4',
    'H5',
    'H6',
    'HEAD',
    'HR',
    'HTML',
    'I',
    'IFRAME',
    'IMG',
    'INPUT',
    'INS',
    'ISINDEX',
    'KBD',
    'LABEL',
    'LEGEND',
    'LI',
    'LINK',
    'MAP',
    'MENU',
    'META',
    'NOFRAMES',
    'NOSCRIPT',
    'OBJECT',
    'OL',
    'OPTGROUP',
    'OPTION',
    'P',
    'PARAM',
    'PRE',
    'Q',
    'S',
    'SAMP',
    'SCRIPT',
    'SELECT',
    'SMALL',
    'SPAN',
    'STRIKE',
    'STRONG',
    'STYLE',
    'SUB',
    'SUP',
    'TABLE',
    'TBODY',
    'TD',
    'TEXTAREA',
    'TFOOT',
    'TH',
    'THEAD',
    'TITLE',
    'TR',
    'TT',
    'U',
    'UL',
    'VAR',
]

OPERATING_SYSTEMS = entities._OPERATING_SYSTEMS

TEMPLATE_TYPES = [
    'finish',
    'iPXE',
    'provision',
    'PXEGrub',
    'PXELinux',
    'script',
    'user_data',
    'ZTP',
]

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

KEY_CLOAK_CLI = "/opt/rh/rh-sso7/root/usr/share/keycloak/bin/kcadm.sh"

RPM_TO_UPLOAD = "which-2.19-6.el6.x86_64.rpm"
SRPM_TO_UPLOAD = "which-2.19-6.el6.src.rpm"

ENVIRONMENT = "Library"

NOT_IMPLEMENTED = 'Test not implemented'

SYNC_INTERVAL = {'hour': "hourly", 'day': "daily", 'week': "weekly", 'custom': "custom cron"}

REPO_TYPE = {'yum': "yum", 'puppet': "puppet", 'docker': "docker", 'ostree': "ostree"}

DOWNLOAD_POLICIES = {
    'on_demand': "On Demand",
    'background': "Background",
    'immediate': "Immediate",
}

CHECKSUM_TYPE = {'default': "Default", 'sha256': "sha256", 'sha1': "sha1"}

HASH_TYPE = {'sha256': "SHA256", 'sha512': "SHA512", 'base64': "Base64", 'md5': "MD5"}

REPO_TAB = {'rpms': "RPMs", 'kickstarts': "Kickstarts", 'isos': "ISOs", 'ostree': "OSTree"}

# On importing manifests, Red Hat repositories are listed like this:
# Product -> RepositorySet -> Repository
# We need to first select the Product, then the reposet and then the repos
# Example: 'rhel' is the name of Product that contains following REPOSETs
PRDS = {
    'rhcf': 'Red Hat CloudForms',
    'rhel': 'Red Hat Enterprise Linux Server',
    'rhah': 'Red Hat Enterprise Linux Atomic Host',
    'rhsc': 'Red Hat Satellite Capsule',
    'rhdt': 'Red Hat Developer Tools for RHEL Server',
    'rhscl': 'Red Hat Software Collections (for RHEL Server)',
    'rhae': 'Red Hat Ansible Engine',
}

REPOSET = {
    'rhct6': 'Red Hat CloudForms Tools for RHEL 6 (RPMs)',
    'rhel6': 'Red Hat Enterprise Linux 6 Server (RPMs)',
    'rhel7': 'Red Hat Enterprise Linux 7 Server (RPMs)',
    'rhva6': ('Red Hat Enterprise Virtualization Agents for RHEL 6 Server (RPMs)'),
    'rhsc7': 'Red Hat Satellite Capsule 6.6 (for RHEL 7 Server) (RPMs)',
    'rhsc7_iso': 'Red Hat Satellite Capsule 6.6 (for RHEL 7 Server) (ISOs)',
    'rhsc6': 'Red Hat Satellite Capsule 6.6 (for RHEL 6 Server) (RPMs)',
    'rhst7': 'Red Hat Satellite Tools 6.7 (for RHEL 7 Server) (RPMs)',
    'rhst7_64': 'Red Hat Satellite Tools 6.4 (for RHEL 7 Server) (RPMs)',
    'rhst7_65': 'Red Hat Satellite Tools 6.5 (for RHEL 7 Server) (RPMs)',
    'rhst7_66': 'Red Hat Satellite Tools 6.6 (for RHEL 7 Server) (RPMs)',
    'rhst7_67': 'Red Hat Satellite Tools 6.7 (for RHEL 7 Server) (RPMs)',
    'rhst6': 'Red Hat Satellite Tools 6.6 (for RHEL 6 Server) (RPMs)',
    'rhaht': 'Red Hat Enterprise Linux Atomic Host (Trees)',
    'rhdt7': ('Red Hat Developer Tools RPMs for Red Hat Enterprise Linux 7 Server'),
    'rhscl7': ('Red Hat Software Collections RPMs for Red Hat Enterprise Linux 7 Server'),
    'rhae2': 'Red Hat Ansible Engine 2.7 RPMs for Red Hat Enterprise Linux 7 Server',
}

NO_REPOS_AVAILABLE = "This system has no repositories available through subscriptions."

SM_OVERALL_STATUS = {
    'current': 'Overall Status: Current',
    'invalid': 'Overall Status: Invalid',
    'insufficient': 'Overall Status: Insufficient',
    'unknown': 'Overall Status: Unknown',
}

REPOS = {
    'rhel7': {
        'id': 'rhel-7-server-rpms',
        'name': 'Red Hat Enterprise Linux 7 Server RPMs x86_64 7Server',
        'releasever': '7Server',
        'arch': 'x86_64',
        'distro': DISTRO_RHEL7,
        'reposet': REPOSET['rhel7'],
        'product': PRDS['rhel'],
        'major_version': RHEL_7_MAJOR_VERSION,
        'distro_repository': True,
        'key': 'rhel',
        'version': '7.7',
    },
    'rhel6': {
        'id': 'rhel-6-server-rpms',
        'name': 'Red Hat Enterprise Linux 6 Server RPMs x86_64 6Server',
        'releasever': '6Server',
        'arch': 'x86_64',
        'distro': DISTRO_RHEL6,
        'reposet': REPOSET['rhel6'],
        'product': PRDS['rhel'],
        'major_version': RHEL_6_MAJOR_VERSION,
        'distro_repository': True,
        'key': 'rhel',
        'version': '6.8',
    },
    'rhsc7': {
        'id': 'rhel-7-server-satellite-capsule-6.6-rpms',
        'name': ('Red Hat Satellite Capsule 6.6 for RHEL 7 Server RPMs x86_64'),
        'version': '6.6',
        'reposet': REPOSET['rhsc7'],
        'product': PRDS['rhsc'],
        'distro': DISTRO_RHEL7,
        'key': 'rhsc',
    },
    'rhsc7_iso': {
        'id': 'rhel-7-server-satellite-capsule-6.6-isos',
        'name': ('Red Hat Satellite Capsule 6.6 for RHEL 7 Server ISOs x86_64'),
    },
    'rhsc6': {
        'id': 'rhel-6-server-satellite-capsule-6.6-rpms',
        'name': ('Red Hat Satellite Capsule 6.6 for RHEL 6 Server RPMs x86_64'),
        'version': '6.6',
        'reposet': REPOSET['rhsc6'],
        'product': PRDS['rhsc'],
        'distro': DISTRO_RHEL6,
        'key': 'rhsc',
    },
    'rhst7': {
        'id': 'rhel-7-server-satellite-tools-6.7-rpms',
        'name': ('Red Hat Satellite Tools 6.7 for RHEL 7 Server RPMs x86_64'),
        'version': '6.7',
        'reposet': REPOSET['rhst7'],
        'product': PRDS['rhel'],
        'distro': DISTRO_RHEL7,
        'key': 'rhst',
    },
    'rhst7_64': {
        'id': 'rhel-7-server-satellite-tools-6.4-rpms',
        'name': ('Red Hat Satellite Tools 6.4 for RHEL 7 Server RPMs x86_64'),
        'version': '6.4',
        'reposet': REPOSET['rhst7_64'],
        'product': PRDS['rhel'],
        'distro': DISTRO_RHEL7,
        'key': 'rhst',
    },
    'rhst7_65': {
        'id': 'rhel-7-server-satellite-tools-6.5-rpms',
        'name': ('Red Hat Satellite Tools 6.5 for RHEL 7 Server RPMs x86_64'),
        'version': '6.5',
        'reposet': REPOSET['rhst7_65'],
        'product': PRDS['rhel'],
        'distro': DISTRO_RHEL7,
        'key': 'rhst',
    },
    'rhst7_66': {
        'id': 'rhel-7-server-satellite-tools-6.6-rpms',
        'name': ('Red Hat Satellite Tools 6.6 for RHEL 7 Server RPMs x86_64'),
        'version': '6.6',
        'reposet': REPOSET['rhst7_66'],
        'product': PRDS['rhel'],
        'distro': DISTRO_RHEL7,
        'key': 'rhst',
    },
    'rhst7_67': {
        'id': 'rhel-7-server-satellite-tools-6.7-rpms',
        'name': ('Red Hat Satellite Tools 6.7 for RHEL 7 Server RPMs x86_64'),
        'version': '6.7',
        'reposet': REPOSET['rhst7_67'],
        'product': PRDS['rhel'],
        'distro': DISTRO_RHEL7,
        'key': 'rhst',
    },
    'rhst6': {
        'id': 'rhel-6-server-satellite-tools-6.6-rpms',
        'name': ('Red Hat Satellite Tools 6.6 for RHEL 6 Server RPMs x86_64'),
        'version': '6.6',
        'reposet': REPOSET['rhst6'],
        'product': PRDS['rhel'],
        'distro': DISTRO_RHEL6,
        'key': 'rhst',
    },
    'rhva6': {
        'id': 'rhel-6-server-rhev-agent-rpms',
        'name': ('Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs x86_64 6Server'),
        'version': '6.0',
        'reposet': REPOSET['rhva6'],
        'product': PRDS['rhel'],
        'distro': DISTRO_RHEL6,
        'releasever': '6Server',
        'key': 'rhva6',
    },
    'rhva65': {
        'name': ('Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs x86_64 6.5'),
        'version': '6.5',
        'reposet': REPOSET['rhva6'],
        'product': PRDS['rhel'],
        'distro': DISTRO_RHEL6,
        'key': 'rhva65',
    },
    'rhct6': {
        'name': 'Red Hat CloudForms Tools for RHEL 6 RPMs x86_64 6Server',
        'releasever': '6Server',
        'version': '6Server',
        'arch': 'x86_64',
        'reposet': REPOSET['rhct6'],
        'product': PRDS['rhel'],
        'distro': DISTRO_RHEL6,
        'key': 'rhct6',
    },
    'rhaht': {'name': ('Red Hat Enterprise Linux Atomic Host Trees')},
    'rhdt7': {
        'name': ('Red Hat Developer Tools RPMs for Red Hat Enterprise Linux 7 Server x86_64')
    },
    'rhscl7': {
        'id': 'rhel-server-rhscl-7-rpms',
        'name': (
            'Red Hat Software Collections RPMs for Red Hat Enterprise'
            ' Linux 7 Server x86_64 7Server'
        ),
    },
    'rhae2': {
        'id': 'rhel-7-server-ansible-2.7-rpms',
        'name': 'Red Hat Ansible Engine 2.7 RPMs for Red Hat Enterprise Linux 7 Server x86_64',
        'version': '2.7',
        'arch': 'x86_64',
        'reposet': REPOSET['rhae2'],
        'product': PRDS['rhae'],
        'distro': DISTRO_RHEL7,
        'key': 'rhae2',
    },
}

DISTRO_REPOS = {
    # DISTRO_RHEL6: REPOS['rhel6'],
    DISTRO_RHEL7: REPOS['rhel7']
}

# The 'create_repos_tree' function under 'sync' module uses the following
# list of tuples. It actually includes following two repos under
# Reposet: Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs
#
# Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs x86_64 6.5
# Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs x86_64
# 6Server

RHVA_REPO_TREE = [
    (
        'rhel',
        'rhva6',
        'rhva65',
        'repo_name',
        'Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs x86_64 6.5',
    ),
    ('rhel', 'rhva6', 'rhva65', 'repo_arch', 'x86_64'),
    ('rhel', 'rhva6', 'rhva65', 'repo_ver', '6.5'),
    (
        'rhel',
        'rhva6',
        'rhva6S',
        'repo_name',
        'Red Hat Enterprise Virtualization Agents for RHEL 6 Server RPMs x86_64 6Server',
    ),
    ('rhel', 'rhva6', 'rhva6S', 'repo_arch', 'x86_64'),
    ('rhel', 'rhva6', 'rhva6S', 'repo_ver', '6Server'),
]

SAT6_TOOLS_TREE = [
    (
        'rhel',
        'rhst6',
        'rhst6',
        'repo_name',
        'Red Hat Satellite Tools 6.6 for RHEL 6 Server RPMs x86_64',
    ),
    ('rhel', 'rhst6', 'rhst6', 'repo_arch', 'x86_64'),
    ('rhel', 'rhst6', 'rhst6', 'repo_ver', '6.6'),
]

ATOMIC_HOST_TREE = [
    ('rhah', 'rhaht', 'rhaht', 'repo_name', 'Red Hat Enterprise Linux Atomic Host Trees'),
    ('rhah', 'rhaht', 'rhaht', 'repo_arch', None),
    ('rhah', 'rhaht', 'rhaht', 'repo_ver', None),
]
#: Name (not label!) of the default organization.
DEFAULT_ORG = "Default Organization"
#: Name (not label!) of the default location.
DEFAULT_LOC = "Default Location"
DEFAULT_CV = "Default Organization View"
DEFAULT_TEMPLATE = "Kickstart default"
DEFAULT_PXE_TEMPLATE = "Kickstart default PXELinux"
DEFAULT_ATOMIC_TEMPLATE = 'Atomic Kickstart default'
DEFAULT_PTABLE = "Kickstart default"
DEFAULT_SUBSCRIPTION_NAME = 'Red Hat Enterprise Linux Server, Premium (Physical or Virtual Nodes)'
DEFAULT_ARCHITECTURE = 'x86_64'
DEFAULT_RELEASE_VERSION = '6Server'
DEFAULT_ROLE = 'Default role'

LANGUAGES = {
    'Català': 'ca',
    'Deutsch': 'de',
    'English (United States)': 'en',
    'English (United Kingdom)': 'en_GB',
    'Español': 'es',
    'Français': 'fr',
    'Galego': 'gl',
    'it': 'it',
    '日本語': 'ja',
    '한국어': 'ko',
    'pl': 'pl',
    'Português (Brasil)': 'pt_BR',
    'Русский': 'ru',
    'sv_SE': 'sv_SE',
    '简体中文': 'zh_CN',
    'zh_TW': 'zh_TW',
}

SATELLITE_SUBSCRIPTION_NAME = 'Red Hat Satellite Infrastructure Subscription'
SATELLITE_FIREWALL_SERVICE_NAME = 'RH-Satellite-6'
VDC_SUBSCRIPTION_NAME = 'Red Hat Enterprise Linux for Virtual Datacenters, Premium'

TIMEZONES = [
    '(GMT+00:00) UTC',
    '(GMT-10:00) Hawaii',
    '(GMT+02:00) Kyiv',
    '(GMT+08:00) Hong Kong',
    '(GMT-07:00) Arizona',
]

FILTER_CONTENT_TYPE = {
    'package': "Package",
    'package group': "Package Group",
    'erratum by id': "Erratum - by ID",
    'erratum by date and type': "Erratum - Date and Type",
    'modulemd': "Module Stream",
}

FILTER_TYPE = {'include': "Include", 'exclude': "Exclude"}

FILTER_ERRATA_TYPE = {
    'security': "security",
    'enhancement': "enhancement",
    'bugfix': "bugfix",
    'all': 'all',
    'recommended': 'recommended',
    'optional': 'optional',
}

FILTER_ERRATA_DATE = {'updated': "updated", 'issued': "issued"}

REPORT_TEMPLATE_FILE = 'report_template.txt'
REP_TEM_APPLIED_ERRATA_INPUT = {
    'Filter Errata Type': FILTER_ERRATA_TYPE,
    'Status': {
        'success': 'success',
        'warning': 'warning',
        'error': 'error',
        'canceled': 'canceled',
        'pending': 'pending',
    },
    'Include Last Reboot': {'yes': 'yes', 'no': 'no'},
}

DOCKER_REGISTRY_HUB = 'https://registry-1.docker.io'
DOCKER_UPSTREAM_NAME = 'busybox'
DOCKER_RH_REGISTRY_UPSTREAM_NAME = 'openshift3/ose-metrics-hawkular-openshift-agent'
CUSTOM_FILE_REPO = 'https://repos.fedorapeople.org/repos/pulp/pulp/fixtures/file/'
CUSTOM_LOCAL_FOLDER = '/var/www/html/myrepo/'
CUSTOM_LOCAL_FILE = '/var/www/html/myrepo/test.txt'
CUSTOM_FILE_REPO_FILES_COUNT = 3

CUSTOM_KICKSTART_REPO = 'http://mirror.linux.duke.edu/pub/centos/8/BaseOS/x86_64/kickstart/'

CUSTOM_RPM_REPO = 'http://repos.fedorapeople.org/repos/pulp/pulp/fixtures/rpm/'

CUSTOM_RPM_SHA_512 = 'https://repos.fedorapeople.org/pulp/pulp/fixtures/rpm-with-sha-512/'

CUSTOM_RPM_SHA_512_FEED_COUNT = {'rpm': 35, 'errata': 4}

CUSTOM_MODULE_STREAM_REPO_1 = 'https://partha.fedorapeople.org/test-repos/pteradactyl/'
CUSTOM_MODULE_STREAM_REPO_2 = 'https://partha.fedorapeople.org/test-repos/rpm-with-modules/el8/'
CUSTOM_SWID_TAG_REPO = 'https://partha.fedorapeople.org/test-repos/swid-zoo/'
CUSTOM_REPODATA_PATH = '/var/lib/pulp/published/yum/https/repos'
CERT_PATH = "/etc/pki/ca-trust/source/anchors/"
FAKE_0_YUM_REPO = 'http://inecas.fedorapeople.org/fakerepos/zoo/'
FAKE_1_YUM_REPO = 'http://inecas.fedorapeople.org/fakerepos/zoo3/'
FAKE_2_YUM_REPO = 'http://inecas.fedorapeople.org/fakerepos/zoo2/'
FAKE_3_YUM_REPO = 'http://omaciel.fedorapeople.org/fakerepo01'
FAKE_4_YUM_REPO = 'http://omaciel.fedorapeople.org/fakerepo02'
FAKE_5_YUM_REPO = 'http://{0}:{1}@rplevka.fedorapeople.org/fakerepo01/'
FAKE_6_YUM_REPO = 'https://stephenw.fedorapeople.org/fakerepos/needed-errata/'
FAKE_7_YUM_REPO = 'https://repos.fedorapeople.org/pulp/pulp/demo_repos/large_errata/zoo/'
FAKE_8_YUM_REPO = 'https://abalakht.fedorapeople.org/test_repos/lots_files/'
FAKE_9_YUM_REPO = 'https://stephenw.fedorapeople.org/fakerepos/multiple_errata/'
FAKE_10_YUM_REPO = 'https://partha.fedorapeople.org/test-repos/separated/modules-rpms/'
FAKE_11_YUM_REPO = 'https://partha.fedorapeople.org/test-repos/separated/rpm-deps/'
FAKE_YUM_DRPM_REPO = 'https://repos.fedorapeople.org/repos/pulp/pulp/fixtures/drpm/'
FAKE_YUM_SRPM_REPO = 'https://repos.fedorapeople.org/repos/pulp/pulp/fixtures/srpm/'
FAKE_YUM_SRPM_DUPLICATE_REPO = 'https://repos.fedorapeople.org/pulp/pulp/fixtures/srpm-duplicate/'
FAKE_YUM_MIXED_REPO = 'https://pondrejk.fedorapeople.org/test_repos/mixed/'
FAKE_0_YUM_REPO_PACKAGES_COUNT = 32
CUSTOM_PUPPET_REPO = 'http://omaciel.fedorapeople.org/bagoftricks'
FAKE_0_PUPPET_REPO = 'http://davidd.fedorapeople.org/repos/random_puppet/'
FAKE_1_PUPPET_REPO = 'http://omaciel.fedorapeople.org/fakepuppet01'
FAKE_2_PUPPET_REPO = 'http://omaciel.fedorapeople.org/fakepuppet02'
FAKE_3_PUPPET_REPO = 'http://omaciel.fedorapeople.org/fakepuppet03'
FAKE_4_PUPPET_REPO = 'http://omaciel.fedorapeople.org/fakepuppet04'
FAKE_5_PUPPET_REPO = 'http://omaciel.fedorapeople.org/fakepuppet05'
FAKE_6_PUPPET_REPO = 'http://kbidarka.fedorapeople.org/repos/puppet-modules/'
FAKE_7_PUPPET_REPO = 'http://{0}:{1}@rplevka.fedorapeople.org/fakepuppet01/'
FAKE_8_PUPPET_REPO = 'https://omaciel.fedorapeople.org/f4cb00ed/'
# Fedora's OSTree repo changed to a single repo at
#   https://kojipkgs.fedoraproject.org/compose/ostree/repo/
# With branches for each version. Some tests (test_positive_update_url) still need 2 repos URLs,
# We will use the archived versions for now, but probably need to revisit this.
FEDORA26_OSTREE_REPO = 'https://kojipkgs.fedoraproject.org/compose/ostree-20190207-old/26/'
FEDORA27_OSTREE_REPO = 'https://kojipkgs.fedoraproject.org/compose/ostree-20190207-old/27/'
REPO_DISCOVERY_URL = 'http://omaciel.fedorapeople.org/'
FAKE_0_INC_UPD_URL = 'https://abalakht.fedorapeople.org/test_files/inc_update/'
FAKE_0_INC_UPD_ERRATA = 'EXA:2015-0002'
FAKE_0_INC_UPD_OLD_PACKAGE = 'pulp-test-package-0.2.1-1.fc11.x86_64.rpm'
FAKE_0_INC_UPD_NEW_PACKAGE = 'pulp-test-package-0.3.1-1.fc11.x86_64.rpm'
FAKE_0_INC_UPD_OLD_UPDATEFILE = 'updateinfo.xml'
FAKE_0_INC_UPD_NEW_UPDATEFILE = 'updateinfo_v2.xml'
INVALID_URL = 'http://username:password@@example.com/repo'
FAKE_0_CUSTOM_PACKAGE = 'bear-4.1-1.noarch'
FAKE_0_CUSTOM_PACKAGE_NAME = 'bear'
FAKE_1_CUSTOM_PACKAGE = 'walrus-0.71-1.noarch'
FAKE_1_CUSTOM_PACKAGE_NAME = 'walrus'
FAKE_2_CUSTOM_PACKAGE = 'walrus-5.21-1.noarch'
FAKE_2_CUSTOM_PACKAGE_NAME = 'walrus'
FAKE_3_CUSTOM_PACKAGE = 'duck-0.8-1.noarch'
FAKE_3_CUSTOM_PACKAGE_NAME = 'duck'
FAKE_4_CUSTOM_PACKAGE = 'kangaroo-0.2-1.noarch'  # for RHBA-2012:1030
FAKE_4_CUSTOM_PACKAGE_NAME = 'kangaroo'
FAKE_5_CUSTOM_PACKAGE = 'kangaroo-0.3-1.noarch'  # for RHBA-2012:1030
REAL_0_RH_PACKAGE = 'rhevm-sdk-python-3.3.0.21-1.el6ev.noarch'
REAL_RHEL7_0_0_PACKAGE = 'liblouis-python-2.5.2-10.el7.noarch'
REAL_RHEL7_0_0_PACKAGE_NAME = 'liblouis-python'
REAL_RHEL7_0_1_PACKAGE = 'liblouis-python-2.5.2-11.el7_4.noarch'
REAL_RHEL7_0_1_PACKAGE_FILENAME = 'liblouis-python-2.5.2-11.el7_4.noarch.rpm'
FAKE_0_CUSTOM_PACKAGE_GROUP_NAME = 'birds'
FAKE_9_YUM_OUTDATED_PACKAGES = [
    'bear-4.0-1.noarch',
    'crow-0.7-1.noarch',
    'duck-0.5-1.noarch',
    'gorilla-0.61-1.noarch',
    'penguin-0.8.1-1.noarch',
    'stork-0.11-1.noarch',
    'walrus-0.71-1.noarch',
    'kangaroo-0.2-1.noarch',
]
FAKE_9_YUM_UPDATED_PACKAGES = [
    'bear-4.1-1.noarch',
    'crow-0.8-1.noarch',
    'duck-0.6-1.noarch',
    'gorilla-0.62-1.noarch',
    'penguin-0.9.1-1.noarch',
    'stork-0.12-1.noarch',
    'walrus-5.21-1.noarch',
    'kangaroo-0.3-1.noarch',
]
FAKE_0_MODULAR_ERRATA_ID = 'RHEA-2012:0059'
FAKE_0_ERRATA_ID = 'RHEA-2012:0001'
FAKE_1_ERRATA_ID = 'RHEA-2012:0002'
FAKE_2_ERRATA_ID = 'RHSA-2012:0055'  # for FAKE_6_YUM_REPO and FAKE_9_YUM_REPO
FAKE_3_ERRATA_ID = 'RHEA-2012:7269'  # for FAKE_3_YUM_REPO
FAKE_4_ERRATA_ID = 'WALRUS-2013:0002'
FAKE_5_ERRATA_ID = 'RHBA-2012:1030'  # for FAKE_6_YUM_REPO and FAKE_9_YUM_REPO
REAL_0_ERRATA_ID = 'RHBA-2019:3175'  # for rhst7
REAL_1_ERRATA_ID = 'RHBA-2016:1357'  # for REAL_0_RH_PACKAGE
REAL_2_ERRATA_ID = 'RHEA-2014:0657'  # for REAL_0_RH_PACKAGE
REAL_4_ERRATA_ID = 'RHSA-2014:1873'  # for rhva6 with type=security and cves
REAL_4_ERRATA_CVES = ['CVE-2014-3633', 'CVE-2014-3657', 'CVE-2014-7823']
REAL_RHEL7_0_ERRATA_ID = 'RHSA-2017:3111'  # for REAL_RHEL7_0_0_PACKAGE
REAL_RHEL7_1_ERRATA_ID = 'RHBA-2017:0395'  # tcsh bug fix update
FAKE_0_YUM_ERRATUM_COUNT = 4
FAKE_1_YUM_ERRATUM_COUNT = 4
FAKE_1_YUM_REPOS_COUNT = 32
FAKE_3_YUM_ERRATUM_COUNT = 79
FAKE_3_YUM_REPOS_COUNT = 136
FAKE_6_YUM_ERRATUM_COUNT = 5
FAKE_9_YUM_ERRATUM_COUNT = 5
FAKE_9_YUM_ERRATUM = [
    'RHSA-2012:0055',
    'RHSA-2012:0056',
    'RHSA-2012:0057',
    'RHEA-2012:0058',
    'RHBA-2012:1030',
]
FAKE_9_YUM_SECURITY_ERRATUM = [
    'RHSA-2012:0055',
    'RHSA-2012:0056',
    'RHSA-2012:0057',
]
FAKE_9_YUM_SECURITY_ERRATUM_COUNT = len(FAKE_9_YUM_SECURITY_ERRATUM)

FAKE_10_YUM_BUGFIX_ERRATUM = [
    'RHBA-2012:1030',
]
FAKE_10_YUM_BUGFIX_ERRATUM_COUNT = len(FAKE_10_YUM_BUGFIX_ERRATUM)

FAKE_11_YUM_ENHANCEMENT_ERRATUM = [
    'RHEA-2012:0058',
]
FAKE_11_YUM_ENHANCEMENT_ERRATUM_COUNT = len(FAKE_11_YUM_ENHANCEMENT_ERRATUM)

PUPPET_MODULE_NTP_PUPPETLABS = "puppetlabs-ntp-3.2.1.tar.gz"

PUPPET_MODULE_CUSTOM_FILE_NAME = 'puppet_custom_selinux-0.3.1.tar.gz'
PUPPET_MODULE_CUSTOM_NAME = 'selinux'

FAKE_0_CUSTOM_PACKAGE_GROUP = [
    'cockateel-3.1-1.noarch',
    'duck-0.6-1.noarch',
    'penguin-0.9.1-1.noarch',
    'stork-0.12-2.noarch',
]

FAKE_1_YUM_REPO_RPMS = ['bear-4.1-1.noarch.rpm', 'camel-0.1-1.noarch.rpm', 'cat-1.0-1.noarch.rpm']
FAKE_0_PUPPET_MODULE = 'httpd'

FAKE_PULP_REMOTE_FILEREPO = 'https://pondrejk.fedorapeople.org/test_repos/filerepo/'

FAKE_0_YUM_REPO_STRING_BASED_VERSIONS = (
    'https://repos.fedorapeople.org/pulp/pulp/fixtures/rpm-string-version-updateinfo/'
)
FAKE_0_YUM_REPO_STRING_BASED_VERSIONS_COUNTS = {'rpm': 35, 'package_group': 2, 'erratum': 4}

PULP_PUBLISHED_ISO_REPOS_PATH = '/var/lib/pulp/published/http/isos'
PULP_PUBLISHED_PUPPET_REPOS_PATH = '/var/lib/pulp/published/puppet/https/repos'
PULP_PUBLISHED_YUM_REPOS_PATH = '/var/lib/pulp/published/yum/http/repos'

#: All permissions exposed by the server.
#: :mod:`tests.foreman.api.test_permission` makes use of this.
PERMISSIONS = {
    None: [
        'access_dashboard',
        'app_root',
        'attachments',
        'configuration',
        'create_arf_reports',
        'create_recurring_logics',
        'destroy_arf_reports',
        'destroy_config_reports',
        'download_bootdisk',
        'edit_recurring_logics',
        'escalate_roles',
        'generate_ansible_inventory',
        'logs',
        'my_organizations',
        'rh_telemetry_api',
        'rh_telemetry_configurations',
        'rh_telemetry_view',
        'strata_api',
        'upload_config_reports',
        'view_arf_reports',
        'view_cases',
        'view_config_reports',
        'view_log_viewer',
        'view_plugins',
        'view_recurring_logics',
        'view_statistics',
        'view_rh_search',
        'view_tasks',
        'view_statuses',
    ],
    'AnsibleRole': ['view_ansible_roles', 'destroy_ansible_roles', 'import_ansible_roles'],
    'AnsibleVariable': [
        'edit_ansible_variables',
        'view_ansible_variables',
        'import_ansible_variables',
        'destroy_ansible_variables',
        'create_ansible_variables',
    ],
    'Architecture': [
        'view_architectures',
        'create_architectures',
        'edit_architectures',
        'destroy_architectures',
    ],
    'Audit': ['view_audit_logs'],
    'AuthSource': [
        'view_authenticators',
        'create_authenticators',
        'edit_authenticators',
        'destroy_authenticators',
    ],
    'Bookmark': ['view_bookmarks', 'create_bookmarks', 'edit_bookmarks', 'destroy_bookmarks'],
    'ConfigGroup': [
        'view_config_groups',
        'create_config_groups',
        'edit_config_groups',
        'destroy_config_groups',
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
    'Domain': ['view_domains', 'create_domains', 'edit_domains', 'destroy_domains'],
    'Environment': [
        'view_environments',
        'create_environments',
        'edit_environments',
        'destroy_environments',
        'import_environments',
    ],
    'ExternalUsergroup': [
        'view_external_usergroups',
        'create_external_usergroups',
        'edit_external_usergroups',
        'destroy_external_usergroups',
    ],
    'FactValue': ['view_facts', 'upload_facts'],
    'Filter': ['view_filters', 'create_filters', 'edit_filters', 'destroy_filters'],
    'ForemanTasks::RecurringLogic': [
        'create_recurring_logics',
        'view_recurring_logics',
        'edit_recurring_logics',
    ],
    'ForemanOpenscap::ArfReport': [
        'create_arf_reports',
        'view_arf_reports',
        'destroy_arf_reports',
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
    'ForemanTasks::Task': ['edit_foreman_tasks', 'view_foreman_tasks'],
    'JobInvocation': ['view_job_invocations', 'create_job_invocations', 'cancel_job_invocations'],
    'JobTemplate': [
        'view_job_templates',
        'edit_job_templates',
        'destroy_job_templates',
        'create_job_templates',
        'lock_job_templates',
    ],
    'ConfigReport': ['destroy_config_reports', 'view_config_reports', 'upload_config_reports'],
    'ForemanVirtWhoConfigure::Config': [
        "view_virt_who_config",
        "create_virt_who_config",
        "edit_virt_who_config",
        "destroy_virt_who_config",
    ],
    "ForemanOpenscap::TailoringFile": [
        "create_tailoring_files",
        "view_tailoring_files",
        "edit_tailoring_files",
        "destroy_tailoring_files",
    ],
    'HostClass': ['edit_classes'],
    'Hostgroup': [
        'view_hostgroups',
        'create_hostgroups',
        'edit_hostgroups',
        'destroy_hostgroups',
        'play_roles_on_hostgroup',
    ],
    'HttpProxy': [
        'view_http_proxies',
        'create_http_proxies',
        'edit_http_proxies',
        'destroy_http_proxies',
    ],
    'Image': ['view_images', 'create_images', 'edit_images', 'destroy_images'],
    'KeyPair': ["view_keypairs", "destroy_keypairs"],
    'Location': [
        'view_locations',
        'create_locations',
        'edit_locations',
        'destroy_locations',
        'assign_locations',
    ],
    'MailNotification': ['view_mail_notifications'],
    'Medium': ['view_media', 'create_media', 'edit_media', 'destroy_media'],
    'Model': ['view_models', 'create_models', 'edit_models', 'destroy_models'],
    'Operatingsystem': [
        'view_operatingsystems',
        'create_operatingsystems',
        'edit_operatingsystems',
        'destroy_operatingsystems',
    ],
    'Parameter': ['view_params', 'create_params', 'edit_params', 'destroy_params'],
    'PersonalAccessToken': [
        'view_personal_access_tokens',
        'create_personal_access_tokens',
        'revoke_personal_access_tokens',
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
    'Realm': ['view_realms', 'create_realms', 'edit_realms', 'destroy_realms'],
    'RemoteExecutionFeature': ['edit_remote_execution_features'],
    'Report': ['view_reports', 'destroy_reports', 'upload_reports'],
    'ReportTemplate': [
        'edit_report_templates',
        'destroy_report_templates',
        'generate_report_templates',
        'create_report_templates',
        'view_report_templates',
        'lock_report_templates',
    ],
    'Role': ['view_roles', 'create_roles', 'edit_roles', 'destroy_roles'],
    'Setting': ['view_settings', 'edit_settings'],
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
        'view_capsule_content',
        'view_openscap_proxies',
    ],
    'SshKey': ["view_ssh_keys", "create_ssh_keys", "destroy_ssh_keys"],
    'Subnet': [
        'view_subnets',
        'create_subnets',
        'edit_subnets',
        'destroy_subnets',
        'import_subnets',
    ],
    'Template': ['export_templates', 'import_templates', 'view_template_syncs'],
    'TemplateInvocation': [
        'filter_autocompletion_for_template_invocation',
        'create_template_invocations',
        'view_template_invocations',
    ],
    'Trend': ['view_trends', 'create_trends', 'edit_trends', 'destroy_trends', 'update_trends'],
    'Usergroup': ['view_usergroups', 'create_usergroups', 'edit_usergroups', 'destroy_usergroups'],
    'User': ['view_users', 'create_users', 'edit_users', 'destroy_users'],
    'VariableLookupKey': [
        'view_external_variables',
        'create_external_variables',
        'edit_external_variables',
        'destroy_external_variables',
    ],
    'Host': [
        'auto_provision_discovered_hosts',
        'build_hosts',
        'cockpit_hosts',
        'console_hosts',
        'create_hosts',
        'destroy_discovered_hosts',
        'destroy_hosts',
        'edit_discovered_hosts',
        'edit_hosts',
        'ipmi_boot_hosts',
        'play_roles_on_host',
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
        'view_content_credentials',
        'create_content_credentials',
        'edit_content_credentials',
        'destroy_content_credentials',
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
    'Katello::Subscription': [
        'view_subscriptions',
        'attach_subscriptions',
        'unattach_subscriptions',
        'import_manifest',
        'delete_manifest',
        'manage_subscription_allocations',
    ],
    'Organization': [
        'view_organizations',
        'create_organizations',
        'edit_organizations',
        'destroy_organizations',
        'assign_organizations',
    ],
    'Katello::SyncPlan': [
        'view_sync_plans',
        'create_sync_plans',
        'edit_sync_plans',
        'destroy_sync_plans',
    ],
}

PERMISSIONS_UI = {
    '(Miscellaneous)': [
        'access_dashboard',
        'app_root',
        'attachments',
        'configuration',
        'download_bootdisk',
        'escalate_roles',
        'generate_ansible_inventory',
        'logs',
        'my_organizations',
        'rh_telemetry_api',
        'rh_telemetry_configurations',
        'rh_telemetry_view',
        'view_cases',
        'view_log_viewer',
        'view_plugins',
        'view_statistics',
        'view_rh_search',
        'view_tasks',
        'view_statuses',
    ],
    'Activation Keys': [
        'view_activation_keys',
        'create_activation_keys',
        'edit_activation_keys',
        'destroy_activation_keys',
    ],
    'Architecture': [
        'view_architectures',
        'create_architectures',
        'edit_architectures',
        'destroy_architectures',
    ],
    'Audit': ['view_audit_logs'],
    'Auth source ldap': [
        'view_authenticators',
        'create_authenticators',
        'edit_authenticators',
        'destroy_authenticators',
    ],
    'Bookmark': ['view_bookmarks', 'create_bookmarks', 'edit_bookmarks', 'destroy_bookmarks'],
    'Capsule': [
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
        'view_capsule_content',
        'view_openscap_proxies',
    ],
    'Compute profile': [
        'view_compute_profiles',
        'create_compute_profiles',
        'edit_compute_profiles',
        'destroy_compute_profiles',
    ],
    'Compute resource': [
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
    'Config group': [
        'view_config_groups',
        'create_config_groups',
        'edit_config_groups',
        'destroy_config_groups',
    ],
    'Config report': ['view_config_reports', 'destroy_config_reports', 'upload_config_reports'],
    'Content Views': [
        'view_content_views',
        'create_content_views',
        'edit_content_views',
        'destroy_content_views',
        'publish_content_views',
        'promote_or_remove_content_views',
        'export_content_views',
    ],
    'Discovery rule': [
        'view_discovery_rules',
        'create_discovery_rules',
        'edit_discovery_rules',
        'execute_discovery_rules',
        'destroy_discovery_rules',
    ],
    'Domain': ['view_domains', 'create_domains', 'edit_domains', 'destroy_domains'],
    'Environment': [
        'view_environments',
        'create_environments',
        'edit_environments',
        'destroy_environments',
        'import_environments',
    ],
    'External usergroup': [
        'view_external_usergroups',
        'create_external_usergroups',
        'edit_external_usergroups',
        'destroy_external_usergroups',
    ],
    'Fact value': ['view_facts', 'upload_facts'],
    'Filter': ['view_filters', 'create_filters', 'edit_filters', 'destroy_filters'],
    'GPG Keys': ['view_gpg_keys', 'create_gpg_keys', 'edit_gpg_keys', 'destroy_gpg_keys'],
    'Host': [
        'view_hosts',
        'create_hosts',
        'edit_hosts',
        'destroy_hosts',
        'build_hosts',
        'power_hosts',
        'console_hosts',
        'ipmi_boot_hosts',
        'puppetrun_hosts',
        'view_discovered_hosts',
        'submit_discovered_hosts',
        'auto_provision_discovered_hosts',
        'provision_discovered_hosts',
        'edit_discovered_hosts',
        'destroy_discovered_hosts',
    ],
    'Host Collections': [
        'view_host_collections',
        'create_host_collections',
        'edit_host_collections',
        'destroy_host_collections',
    ],
    'Host Group': [
        'view_hostgroups',
        'create_hostgroups',
        'edit_hostgroups',
        'destroy_hostgroups',
    ],
    'Host сlass': ['edit_classes'],
    'Image': ['view_images', 'create_images', 'edit_images', 'destroy_images'],
    'Job invocation': ['create_job_invocations', 'view_job_invocations'],
    'Job template': [
        'view_job_templates',
        'create_job_templates',
        'edit_job_templates',
        'destroy_job_templates',
        'lock_job_templates',
    ],
    'Key pair': ["view_keypairs", "destroy_keypairs"],
    'Lifecycle Environment': [
        'view_lifecycle_environments',
        'create_lifecycle_environments',
        'edit_lifecycle_environments',
        'destroy_lifecycle_environments',
        'promote_or_remove_content_views_to_environments',
    ],
    'Location': [
        'view_locations',
        'create_locations',
        'edit_locations',
        'destroy_locations',
        'assign_locations',
    ],
    'Mail notification': ['view_mail_notifications'],
    'Medium': ['view_media', 'create_media', 'edit_media', 'destroy_media'],
    'Model': ['view_models', 'create_models', 'edit_models', 'destroy_models'],
    'Operatingsystem': [
        'view_operatingsystems',
        'create_operatingsystems',
        'edit_operatingsystems',
        'destroy_operatingsystems',
    ],
    'Organization': [
        'view_organizations',
        'create_organizations',
        'edit_organizations',
        'destroy_organizations',
        'assign_organizations',
    ],
    'Parameter': ['view_params', 'create_params', 'edit_params', 'destroy_params'],
    'Partition Table': [
        'view_ptables',
        'create_ptables',
        'edit_ptables',
        'destroy_ptables',
        'lock_ptables',
    ],
    'Product and Repositories': [
        'view_products',
        'create_products',
        'edit_products',
        'destroy_products',
        'sync_products',
        'export_products',
    ],
    'Provisioning template': [
        'view_provisioning_templates',
        'create_provisioning_templates',
        'edit_provisioning_templates',
        'destroy_provisioning_templates',
        'deploy_provisioning_templates',
        'lock_provisioning_templates',
    ],
    'Puppet class': [
        'view_puppetclasses',
        'create_puppetclasses',
        'edit_puppetclasses',
        'destroy_puppetclasses',
        'import_puppetclasses',
    ],
    'Realm': ['view_realms', 'create_realms', 'edit_realms', 'destroy_realms'],
    'Remote execution feature': ['edit_remote_execution_features'],
    'Report': ['view_reports', 'destroy_reports', 'upload_reports'],
    'Role': ['view_roles', 'create_roles', 'edit_roles', 'destroy_roles'],
    'Satellite openscap/arf report': [
        'create_arf_reports',
        'view_arf_reports',
        'destroy_arf_reports',
    ],
    'Satellite openscap/policy': [
        'view_policies',
        'edit_policies',
        'create_policies',
        'destroy_policies',
        'assign_policies',
    ],
    'Satellite openscap/scap content': [
        'create_scap_contents',
        'destroy_scap_contents',
        'edit_scap_contents',
        'view_scap_contents',
    ],
    'Satellite openscap/tailoring file': [
        "create_tailoring_files",
        "view_tailoring_files",
        "edit_tailoring_files",
        "destroy_tailoring_files",
    ],
    'Satellite tasks/recurring logic': [
        'create_recurring_logics',
        'view_recurring_logics',
        'edit_recurring_logics',
    ],
    'Satellite tasks/task': ['view_foreman_tasks', 'edit_foreman_tasks'],
    'Satellite virt who configure/config': [
        "view_virt_who_config",
        "create_virt_who_config",
        "edit_virt_who_config",
        "destroy_virt_who_config",
    ],
    'Smart class parameter': [
        'view_external_parameters',
        'create_external_parameters',
        'edit_external_parameters',
        'destroy_external_parameters',
    ],
    'Smart variable': [
        'view_external_variables',
        'create_external_variables',
        'edit_external_variables',
        'destroy_external_variables',
    ],
    'Ssh key': ["view_ssh_keys", "create_ssh_keys", "destroy_ssh_keys"],
    'Subnet': [
        'view_subnets',
        'create_subnets',
        'edit_subnets',
        'destroy_subnets',
        'import_subnets',
    ],
    'Subscription': [
        'view_subscriptions',
        'attach_subscriptions',
        'unattach_subscriptions',
        'import_manifest',
        'delete_manifest',
    ],
    'Sync Plans': [
        'view_sync_plans',
        'create_sync_plans',
        'edit_sync_plans',
        'destroy_sync_plans',
    ],
    'Template invocation': [
        'execute_template_invocation',
        'filter_autocompletion_for_template_invocation',
    ],
    'Trend': ['view_trends', 'create_trends', 'edit_trends', 'destroy_trends', 'update_trends'],
    'User': ['view_users', 'create_users', 'edit_users', 'destroy_users'],
    'Usergroup': ['view_usergroups', 'create_usergroups', 'edit_usergroups', 'destroy_usergroups'],
}


ANY_CONTEXT = {'org': "Any Organization", 'location': "Any Location"}

SUBNET_IPAM_TYPES = {'dhcp': 'DHCP', 'internal': 'Internal DB', 'none': 'None'}

TREND_TYPES = {
    'environment': 'Environment',
    'os': 'Operating system',
    'model': 'Model',
    'facts': 'Facts',
    'host_group': 'Host group',
    'compute_resource': 'Compute resource',
}

LDAP_SERVER_TYPE = {
    'API': {'ipa': 'free_ipa', 'ad': 'active_directory', 'posix': 'posix'},
    'CLI': {'ipa': 'free_ipa', 'ad': 'active_directory', 'posix': 'posix'},
    'UI': {'ipa': 'FreeIPA', 'ad': 'Active Directory', 'posix': 'POSIX'},
}

LDAP_ATTR = {
    'login_ad': 'sAMAccountName',
    'login': 'uid',
    'firstname': 'givenName',
    'surname': 'sn',
    'mail': 'mail',
}

OSCAP_PERIOD = {'weekly': 'Weekly', 'monthly': 'Monthly', 'custom': 'Custom'}

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
    'rhel_firefox': 'Red Hat firefox default content',
}

OSCAP_PROFILE = {
    'c2s_rhel6': 'C2S for Red Hat Enterprise Linux 6',
    'esp': 'Example Server Profile',
    'rhccp': ('Red Hat Corporate Profile for Certified Cloud Providers (RH CCP)'),
    'usgcb': 'United States Government Configuration Baseline (USGCB)',
    'common': 'Common Profile for General-Purpose Systems',
    'firefox': 'Upstream Firefox STIG',
    'tailoring_rhel7': (
        'Standard System Security Profile for Red Hat Enterprise Linux 7 [CUSTOMIZED]'
    ),
    'security6': 'Standard System Security Profile for Red Hat Enterprise Linux 6',
    'security7': 'Standard System Security Profile for Red Hat Enterprise Linux 7',
}

ROLES = [
    'Access Insights Admin',
    'Access Insights Viewer',
    'Ansible Roles Manager',
    'Auditor',
    'Boot disk access',
    'Bookmarks manager',
    'Compliance manager',
    'Compliance viewer',
    'Create ARF report',
    'Discovery Manager',
    'Discovery Reader',
    'Edit hosts',
    'Edit partition tables',
    'Organization admin',
    'Red Hat Access Logs',
    'Register hosts',
    'Remote Execution Manager',
    'Remote Execution User',
    'Site manager',
    'Tasks Manager',
    'Tasks Reader',
    'View hosts',
    'Virt-who Manager',
    'Virt-who Reporter',
    'Virt-who Viewer',
    'Manager',
    'Viewer',
    'System admin',
]

ROLES_UNLOCKED = [
    'Access Insights Admin',
    'Access Insights Viewer',
    'Boot disk access',
    'Compliance manager',
    'Compliance viewer',
    'Red Hat Access Logs',
    'Remote Execution Manager',
    'Remote Execution User',
    'Tasks Manager',
    'Tasks Reader',
]

ROLES_LOCKED = [
    'Discovery Manager',
    'Discovery Reader',
    'Edit hosts',
    'Edit partition tables',
    'Manager',
    'Site manager',
    'View hosts',
    'Viewer',
]

BOOKMARK_ENTITIES = [
    {'name': 'ActivationKey', 'controller': 'katello_activation_keys'},
    {'name': 'Dashboard', 'controller': 'dashboard', 'skip_for_ui': True},
    {'name': 'Fact', 'controller': 'fact_values', 'skip_for_ui': True},
    {'name': 'Audit', 'controller': 'audits', 'skip_for_ui': True},
    {'name': 'Report', 'controller': 'config_reports', 'skip_for_ui': True},
    {'name': 'Task', 'controller': 'foreman_tasks_tasks', 'skip_for_ui': True},
    {'name': 'Subscriptions', 'controller': 'katello_subscriptions', 'skip_for_ui': True},
    {'name': 'Product', 'controller': 'katello_products'},
    {'name': 'Repository', 'controller': 'katello_repositories', 'skip_for_ui': True},
    {'name': 'ContentCredential', 'controller': 'katello_gpg_keys'},
    {'name': 'SyncPlan', 'controller': 'katello_sync_plans'},
    {'name': 'ContentView', 'controller': 'katello_content_views'},
    {'name': 'Errata', 'controller': 'katello_errata', 'skip_for_ui': True},
    {'name': 'Package', 'controller': 'katello_erratum_packages', 'skip_for_ui': True},
    {'name': 'PuppetModule', 'controller': 'katello_puppet_modules', 'skip_for_ui': True},
    {'name': 'ContainerImageTag', 'controller': 'katello_docker_tags', 'skip_for_ui': True},
    {'name': 'Host', 'controller': 'hosts', 'setup': entities.Host},
    {'name': 'ContentHost', 'controller': 'hosts', 'skip_for_ui': True},
    {'name': 'HostCollection', 'controller': 'katello_host_collections'},
    {'name': 'Architecture', 'controller': 'architectures'},
    {
        'name': 'HardwareModel',
        'controller': 'models',
        'setup': entities.Model,
        'skip_for_ui': True,
    },
    {
        'name': 'InstallationMedia',
        'controller': 'media',
        'setup': entities.Media,
        'skip_for_ui': True,
    },
    {'name': 'OperatingSystem', 'controller': 'operatingsystems'},
    {
        'name': 'PartitionTable',
        'controller': 'ptables',
        'setup': entities.PartitionTable,
        'skip_for_ui': False,
    },
    {'name': 'ProvisioningTemplate', 'controller': 'provisioning_templates'},
    {
        'name': 'HostGroup',
        'controller': 'hostgroups',
        'setup': entities.HostGroup,
        'skip_for_ui': True,
    },
    {
        'name': 'DiscoveryRule',
        'controller': 'discovery_rules',
        'skip_for_ui': True,
        'setup': entities.DiscoveryRule,
    },
    {
        'name': 'GlobalParameter',
        'controller': 'common_parameters',
        'setup': entities.CommonParameter,
        'skip_for_ui': True,
    },
    {
        'name': 'ConfigGroup',
        'controller': 'config_groups',
        'setup': entities.ConfigGroup,
        'skip_for_ui': True,
    },
    {'name': 'PuppetEnvironment', 'controller': 'environments', 'setup': entities.Environment},
    {'name': 'PuppetClass', 'controller': 'puppetclasses', 'setup': entities.PuppetClass},
    {
        'name': 'SmartVariable',
        'controller': 'lookup_keys',
        'setup': entities.SmartVariable,
        'skip_for_ui': True,
    },
    {'name': 'Roles', 'controller': 'ansible_roles', 'setup': entities.Role},
    {'name': 'Variables', 'controller': 'ansible_variables'},
    {'name': 'SmartProxy', 'controller': 'smart_proxies', 'skip_for_ui': True},
    {
        'name': 'ComputeResource',
        'controller': 'compute_resources',
        'setup': entities.LibvirtComputeResource,
    },
    {'name': 'ComputeProfile', 'controller': 'compute_profiles', 'setup': entities.ComputeProfile},
    {'name': 'Subnet', 'controller': 'subnets', 'setup': entities.Subnet},
    {'name': 'Domain', 'controller': 'domains', 'setup': entities.Domain},
    {'name': 'Realm', 'controller': 'realms', 'setup': entities.Realm, 'skip_for_ui': True},
    {'name': 'Location', 'controller': 'locations'},
    {'name': 'Organization', 'controller': 'organizations'},
    {'name': 'User', 'controller': 'users'},
    {'name': 'UserGroup', 'controller': 'usergroups', 'setup': entities.UserGroup},
    {'name': 'Role', 'controller': 'roles'},
    {'name': 'Settings', 'controller': 'settings', 'skip_for_ui': True},
]

STRING_TYPES = ['alpha', 'numeric', 'alphanumeric', 'latin1', 'utf8', 'cjk', 'html']

REAL_4_ERRATA_DETAILS = [
    ['Advisory', REAL_4_ERRATA_ID],
    ['CVEs', set(REAL_4_ERRATA_CVES)],
    ['Type', 'Security Advisory'],
    ['Severity', 'Moderate'],
    ['Issued', '11/18/14'],
    ['Last Updated On', '11/18/14'],
    ['Reboot Suggested', 'No'],
    [
        'Topic',
        'Updated libvirt packages that fix three security issues and one bug '
        'are now\navailable for Red Hat Enterprise Linux 6.',
    ],
    [
        'Description',
        'The libvirt library is a C API for managing and interacting with the'
        '\nvirtualization capabilities of Linux and other operating systems.',
    ],
    [
        'Solution',
        'Before applying this update, make sure all previously released errata'
        '\nrelevant to your system have been applied.',
    ],
]

TOOLS_ERRATA_DETAILS = [
    ['Advisory', 'RHBA-2016:1503'],
    ['CVEs', 'N/A'],
    ['Type', 'Bug Fix Advisory'],
    ['Severity', 'None'],
    ['Issued', '7/27/16'],
    ['Last Updated On', '7/27/16'],
    ['Reboot Suggested', 'No'],
    ['Topic', 'Red Hat Satellite 6.2 now available for Red Hat Enterprise Linux 6 and 7'],
    ['Description', 'This update provides Satellite 6.2 client tooling'],
    ['Solution', 'Before applying this update, make sure all previously released errata'],
]

TOOLS_ERRATA_TABLE_DETAILS = [
    'RHBA-2016:1503',
    'Satellite 6.2 Tools Release',
    'Bug Fix Advisory',
    'Installable',
    '7/27/16',
]

BACKUP_FILES = [
    'config_files.tar.gz',
    '.config.snar',
    'metadata.yml',
    'mongo_data.tar.gz',
    '.mongo.snar',
    'pgsql_data.tar.gz',
    '.postgres.snar',
    'pulp_data.tar',
    '.pulp.snar',
]

HOT_BACKUP_FILES = [
    'candlepin.dump',
    'config_files.tar.gz',
    '.config.snar',
    'foreman.dump',
    'metadata.yml',
    'mongo_dump',
    'pulp_data.tar',
    '.pulp.snar',
    'pg_globals.dump',
]

VMWARE_CONSTANTS = {
    'cluster': 'Satellite_Engineering',
    'folder': 'vm',
    'guest_os': 'Red Hat Enterprise Linux 7 (64-bit)',
    'scsicontroller': 'LSI Logic Parallel',
    'virtualhw_version': 'Default',
    'pool': 'Resources',
    'network_interface_name': 'VMXNET 3',
    'datastore': 'Local-Ironforge',
    'network_interfaces': 'qe_%s',
}

HAMMER_CONFIG = "~/.hammer/cli.modules.d/foreman.yml"

ANSWERS = '/etc/foreman-installer/scenarios.d/satellite-answers.yaml'

FOREMAN_TEMPLATE_IMPORT_URL = 'https://github.com/SatelliteQE/foreman_templates.git'

FOREMAN_TEMPLATES_COMMUNITY_URL = 'https://github.com/theforeman/community-templates.git'

FOREMAN_TEMPLATE_TEST_TEMPLATE = (
    'https://raw.githubusercontent.com/SatelliteQE/foreman_templates/example/'
    'example_template.erb'
)

DEFAULT_SYSPURPOSE_ATTRIBUTES = {
    'service_level': ('sla', 'Self-Support', 'Standard', 'Premium'),
    'usage_type': ('usage', 'Production', 'Development/Test', 'Disaster Recovery'),
    'role': (
        'role',
        'Red Hat Enterprise Linux Server',
        'Red Hat Enterprise Linux Workstation',
        'Red Hat Enterprise Linux Compute Node',
    ),
}


OPEN_STATUSES = ("NEW", "ASSIGNED", "POST", "MODIFIED")
CLOSED_STATUSES = ("ON_QA", "VERIFIED", "RELEASE_PENDING", "CLOSED")
WONTFIX_RESOLUTIONS = ("WONTFIX", "CANTFIX", "DEFERRED")

GROUP_MEMBERSHIP_MAPPER = {
    "config": {
        "access.token.claim": "true",
        "claim.name": "groups",
        "full.path": "false",
        "id.token.claim": "true",
        "userinfo.token.claim": "true",
    },
    "name": "satellite-groups-mapper",
    "protocol": "openid-connect",
    "protocolMapper": "oidc-group-membership-mapper",
}

AUDIENCE_MAPPER = {
    "config": {
        "access.token.claim": "true",
        "id.token.claim": "false",
        "included.client.audience": "{rhsso_host}-foreman-openidc",
    },
    "name": "satellite-mapper",
    "protocol": "openid-connect",
    "protocolMapper": "oidc-audience-mapper",
}

RHSSO_NEW_USER = {
    "email": "test_user@example.com",
    "emailVerified": "true",
    "enabled": "true",
    "firstName": "first_name",
    "lastName": "last_name",
    "username": "random_name",
}

RHSSO_RESET_PASSWORD = {"temporary": "false", "type": "password", "value": ""}

FOREMAN_ANSIBLE_MODULES = [
    'foreman_architecture',
    'foreman_auth_source_ldap',
    'foreman_bookmark',
    'foreman_compute_attribute',
    'foreman_compute_profile',
    'foreman_compute_resource',
    'foreman_config_group',
    'foreman_domain',
    'foreman_environment',
    'foreman_external_usergroup',
    'foreman_global_parameter',
    'foreman_host',
    'foreman_host_power',
    'foreman_hostgroup',
    'foreman_image',
    'foreman_installation_medium',
    'foreman_job_template',
    'foreman_location',
    'foreman_model',
    'foreman_operatingsystem',
    'foreman_organization',
    'foreman_os_default_template',
    'foreman_provisioning_template',
    'foreman_ptable',
    'foreman_realm',
    'foreman_role',
    'foreman_scap_content',
    'foreman_scap_tailoring_file',
    'foreman_scc_account',
    'foreman_scc_product',
    'foreman_search_facts',
    'foreman_setting',
    'foreman_smart_class_parameter',
    'foreman_snapshot',
    'foreman_subnet',
    'foreman_templates_import',
    'foreman_user',
    'foreman_usergroup',
    'katello_activation_key',
    'katello_content_credential',
    'katello_content_view',
    'katello_content_view_filter',
    'katello_content_view_version',
    'katello_host_collection',
    'katello_lifecycle_environment',
    'katello_manifest',
    'katello_product',
    'katello_repository',
    'katello_repository_set',
    'katello_sync',
    'katello_sync_plan',
    'katello_upload',
    'redhat_manifest',
]

FAM_MODULE_PATH = (
    '/usr/share/ansible/collections/ansible_collections/redhat/satellite/plugins/modules'
)
