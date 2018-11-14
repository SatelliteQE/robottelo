"""Helpers and other code to help test the VirtWho Configure Plugin

"""

import os
import six

from robottelo import ssh
from robottelo.config.base import get_project_root
from six.moves.configparser import ConfigParser

VIRTWHO_CONFIGD="/etc/virt-who.d/"
VIRTWHO_SYSCONFIG="/etc/sysconfig/virt-who"
VIRTWHO_CONFIGD_LOCAL = os.path.join(get_project_root(), 'data', 'virtwho-configs')


class VirtWhoConfigFile(object):

    def __init__(self, server, config_id):
        self.server = server
        self.config_id = config_id
        self.config_file_name = 'virt-who-config-{}.conf'.format(self.config_id)
        self.remote_path = os.path.join(VIRTWHO_CONFIGD, self.config_file_name)
        self.local_path = os.path.join(VIRTWHO_CONFIGD_LOCAL, self.config_file_name)
        self.config = None


    def read(self):
        ssh.download_file(self.remote_path, self.local_path)
        parser = ConfigParser()
        with open(self.local_path) as cf:
            parser.read_file(cf)




