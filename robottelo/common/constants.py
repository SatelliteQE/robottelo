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
          'usergroup_user': "usergroup_user"}

RESOURCE_DEFAULT = "baremetal"

PARTITION_SCRIPT_URL = 'https://gist.github.com/sghai/7822090/raw'

OS_TEMPLATE_URL = 'https://gist.github.com/sghai/8109676/raw'

INSTALL_MEDIUM_URL = "http://mirror.fakeos.org/%s/$major.$minor/os/$arch"

SNIPPET_URL = 'https://gist.github.com/sghai/8434467/raw'
