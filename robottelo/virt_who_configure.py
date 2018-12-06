"""Helpers and other code to help test the VirtWho Configure Plugin

"""

import os
import six
import tempfile
from robottelo.config import settings
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli import virt_who_config

from nailgun import entities

from robottelo import ssh
from robottelo.config.base import get_project_root
from six.moves.configparser import ConfigParser

VIRTWHO_CONFIGD="/etc/virt-who.d/"
VIRTWHO_SYSCONFIG="/etc/sysconfig/virt-who"
VIRTWHO_CONFIGD_LOCAL = os.path.join(get_project_root(), 'data', 'virtwho-configs')




class VirtWhoConfigIncorrectException(Exception):
    """Raised when there was some issue found when verifiying the virt-who config"""
    def __init__(self):
        su





class VirtWhoHypervisorConfig(object):

    def __init__(self, config_id, server=None):
        self.server= server if server else settings.server.hostname
        self.config_id = config_id
        self.config_file_name = 'virt-who-config-{}.conf'.format(self.config_id)
        self.remote_path = os.path.join(VIRTWHO_CONFIGD, self.config_file_name)
        self.configfile_data= self._read_config_file()

    def _read_config_file(self):
        # Read the virt-who-<id> config file)
        local_path = tempfile.mkstemp(suffix=self.config_file_name)[1]
        ssh.download_file(self.remote_path, local_path, hostname=self.server)
        parser = ConfigParser()
        with open(local_path) as local_fp:
            parser.read_file(local_fp)
        return parser



    def delete_configfile(self, restart_virtwho):
        raise NotImplemented

    def verify(self, expected, verify_section_name= True, ignore_fields=[]):
        """

        :param expected: dict to verify against
        :param verify_sysconfig: Whether to verify the config items that live in /etc/sysconfig/virtwho
        :return: list of tuples containing mismatches between the configuration in the form (keyname, expected, actual)
        """
        ignore_fields = set(ignore_fields)
        ignore_fields.update(['rhsm_encrypted_password'])
        verify_errors = []

        expect_section_name = 'virt-who-config-{}'.format(self.config_id)
        section_ok = (not verify_section_name) or (
                    self.configfile_data.has_section(expect_section_name) and (
                        len(self.configfile_data.sections()) == 1) and (
                        len(self.configfile_data.defaults()) == 0))
        if not section_ok:
            verify_errors.append("Expection single section {!r}, got {!r}".format(expect_section_name, self.configfile_data.sections()))
        else:
            for expect_k,expect_v in expected.items():
                actual_v = self.configfile_data[expect_section_name].get(expect_k, None)
                if not actual_v:
                    verify_errors.append("{} section {} does not have field {}".format(
                        self.config_file_name, expect_section_name, expect_k))
                elif expect_v != actual_v:
                    verify_errors.append("{} {}.{} expected {!r}, got {!r}".format(
                        self.config_file_name, expect_section_name, expect_k, expect_v, actual_v))

        return verify_errors








class VirtWhoServerConfig(object):

    def __init__(self, server):
        self.server = server
        self.sysconfig_data = None

    #TODO need to parse sysconfig
    def _read_sysconfig(self):
        pass

    #Verify section name




def encrypt_virt_who_password(password, server=None):
    result = ssh.command('virt-who-password -p {}'.format(password), hostname=server)
    if result.return_code != 0:
        raise CLIReturnCodeError(result.return_code, result.stderr,
                                 "Error running virt-who-password")
    return result.stdout[0]


def make_expected_configfile_section_from_api(vhc, ignore_fields=None):
    """

    :param nailgun.entities.VirtWhoConfig obj
    :return:
    """
    if not ignore_fields:
        ignore_fields = set()
    vhc_entity = vhc.read(ignore=ignore_fields)
    enc_pass = None
    if 'hypervisor_password' not in ignore_fields and hasattr(vhc,'hypervisor_password'):
        # Can't readthis via api, so only check it if the original object has it set.
        enc_pass = encrypt_virt_who_password(vhc.hypervisor_password)

    d = {
        'type': vhc_entity.hypervisor_type,
        'hypervisor_id': vhc_entity.hypervisor_id,
        'owner': vhc_entity.organization.read().label,
        'env': 'Library',  # this doesnt seem to be configurable by the plugin
        'server': vhc_entity.hypervisor_server,
        'username': vhc_entity.hypervisor_username,
        'rhsm_hostname': vhc_entity.satellite_url,
        'rhsm_username': 'virt_who_reporter_{}'.format(vhc_entity.id),
        # 'rhsm_encrypted_password': '', # Cant verify this
        'rhsm_prefix': '/rhsm'
    }

    if enc_pass:
        d['encrypted_password'] = enc_pass

    return d

def deploy_virt_who_config(config_id, org_id):
    return virt_who_config.VirtWhoConfig.deploy({'id':config_id, 'organization-id': org_id})
