# -*- encoding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai

"""
Defines various constants
"""

ROBOTTELO_PROPERTIES = "robottelo.properties"

FOREMAN_PROVIDERS = {
    'libvirt': 'Libvirt',
    'ovirt': 'Ovirt',
    'ec2': 'EC2',
    'vmware': 'Vmware',
    'openstack': 'Openstack',
    'rackspace': 'Rackspace',
    'gce': 'GCE'}

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
FILTER = {'arch_os': "architecture_operatingsystem",
          'cr_org': "compute_resource_organization",
          'env_org': "environment_organization",
          'os_arch': "operatingsystem_architecture",
          'os_ptable': "operatingsystem_ptable",
          'os_medium': "operatingsystem_medium",
          'subnet_org': "subnet_organization",
          'template_os': "config_template_operatingsystem",
          'user_role': "user_role",
          'user_location': "user_location",
          'user_org': "user_organization",
          'role_permission': "filter_permission",
          'role_org': "filter_organization",
          'usergroup_user': "usergroup_user",
          'location_user': "location_user",
          'org_user': "organization_user",
          'org_proxy': "organization_smart_proxy",
          'org_subnet': "organization_subnet",
          'org_resource': "organization_compute_resource",
          'org_media': "organization_medium",
          'org_template': "organization_config_template",
          'org_domain': "organization_domain",
          'org_envs': "organization_environment",
          'org_hostgroup': "organization_hostgroup",
          'org_location': "organization_location",
          'loc_user': "location_user",
          'loc_proxy': "location_smart_proxy",
          'loc_subnet': "location_subnet",
          'loc_resource': "location_compute_resource",
          'loc_media': "location_medium",
          'loc_template': "location_config_template",
          'loc_domain': "location_domain",
          'loc_envs': "location_environment",
          'loc_hostgroup': "location_hostgroup",
          'loc_org': "location_organization",
          'sub_domain': "subnet_domain"}

RESOURCE_DEFAULT = "baremetal"

OS_TEMPLATE_DATA_FILE = "os_template.txt"

DOMAIN = "lab.dom.%s.com"

PARTITION_SCRIPT_DATA_FILE = "partition_script.txt"

SNIPPET_DATA_FILE = "snippet.txt"

SNIPPET_URL = 'https://gist.github.com/sghai/8434467/raw'

INSTALL_MEDIUM_URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"

VALID_GPG_KEY_FILE = "valid_gpg_key.txt"

VALID_GPG_KEY_BETA_FILE = "valid_gpg_key_beta.txt"

RPM_TO_UPLOAD = "which-2.19-6.el6.x86_64.rpm"

ENVIRONMENT = "Library"

NOT_IMPLEMENTED = 'Test not implemented'

SYNC_INTERVAL = {'hour': "hourly",
                 'day': "daily",
                 'week': "weekly"}

REPO_TYPE = {'yum': "yum",
             'puppet': "puppet"}

PRDS = {'rhcf': "Red Hat CloudForms",
        'rhel': "Red Hat Enterprise Linux Server"}

REPOSET = {'rhct6': "Red Hat CloudForms Tools for RHEL 6 (RPMs)",
           'rhel6': "Red Hat Enterprise Linux 6 Server (RPMs)"}

DEFAULT_ORG = "Default_Organization"
DEFAULT_LOC = "Default_Location"
DEFAULT_CV = "Default Organization View"

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

GOOGLE_CHROME_REPO = u'http://dl.google.com/linux/chrome/rpm/stable/x86_64'
FAKE_PUPPET_REPO = u'http://davidd.fedorapeople.org/repos/random_puppet/'
FAKE_1_YUM_REPO = "http://inecas.fedorapeople.org/fakerepos/zoo3/"
FAKE_2_YUM_REPO = "http://inecas.fedorapeople.org/fakerepos/zoo2/"
REPO_DISCOVERY_URL = "http://omaciel.fedorapeople.org/"
