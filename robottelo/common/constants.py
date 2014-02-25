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
    'Archlinux',
    'Debian',
    'Gentoo',
    'Redhat',
    'Solaris',
    'Suse',
    'Windows',
]

TEMPLATE_TYPES = [
    'PXELinux',
    'gPXE',
    'provision',
    'finish',
    'script',
    'PXEGrub',
    'snippet',
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
          'usergroup_user': "usergroup_user",
          'org_user': "organization_user",
          'org_proxy': "organization_smart_proxy",
          'org_subnet': "organization_subnet",
          'org_resource': "organization_compute_resource",
          'org_media': "organization_medium",
          'org_template': "organization_config_template",
          'org_domain': "organization_domain",
          'org_envs': "organization_environment",
          'org_hostgroup': "organization_hostgroup"}

RESOURCE_DEFAULT = "baremetal"

OS_TEMPLATE_DATA_FILE = "os_template.txt"

PARTITION_SCRIPT_DATA_FILE = "partition_script.txt"

SNIPPET_DATA_FILE = "snippet.txt"

SNIPPET_URL = 'https://gist.github.com/sghai/8434467/raw'

INSTALL_MEDIUM_URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"

VALID_GPG_KEY_FILE = "valid_gpg_key.txt"

VALID_GPG_KEY_BETA_FILE = "valid_gpg_key_beta.txt"

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

rhcf = [('rhcf', 'rhct6', 'rhct65', 'rhct65_n',
         'Red Hat CloudForms Tools for RHEL 6 RPMs x86_64 6.5'),
        ('rhcf', 'rhct6', 'rhct65', 'rhct65_a', 'x86_64'),
        ('rhcf', 'rhct6', 'rhct65', 'rhct65_v', '6.5'),
        ('rhcf', 'rhct6', 'rhct6S', 'rhct6S_n',
         'Red Hat CloudForms Tools for RHEL 6 RPMs x86_64 6Server'),
        ('rhcf', 'rhct6', 'rhct6S', 'rhct6S_a', 'x86_64'),
        ('rhcf', 'rhct6', 'rhct6S', 'rhct6S_v', '6Server')]

rhel = [('rhel', 'rhel6', 'rhel65', 'rhel65_n',
         'Red Hat Enterprise Linux 6 Server RPMs x86_64 6.5'),
        ('rhel', 'rhel6', 'rhel65', 'rhel65_a', 'x86_64'),
        ('rhel', 'rhel6', 'rhel65', 'rhel65_v', '6.5'),
        ('rhel', 'rhel6', 'rhel6S', 'rhel6S_n',
         'Red Hat Enterprise Linux 6 Server RPMs x86_64 6Server'),
        ('rhel', 'rhel6', 'rhel6S', 'rhel6S_a', 'x86_64'),
        ('rhel', 'rhel6', 'rhel6S', 'rhel6S_v', '6Server')]

DEFAULT_ORG = "ACME"
