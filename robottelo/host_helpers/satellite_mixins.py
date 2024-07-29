import contextlib
from functools import lru_cache
import io
import os
import random
import re

import requests
from wait_for import TimedOutError, wait_for

from robottelo.cli.proxy import CapsuleTunnelError
from robottelo.config import settings
from robottelo.constants import (
    PULP_EXPORT_DIR,
    PULP_IMPORT_DIR,
    PUPPET_COMMON_INSTALLER_OPTS,
    PUPPET_SATELLITE_INSTALLER,
)
from robottelo.exceptions import CLIReturnCodeError
from robottelo.host_helpers.api_factory import APIFactory
from robottelo.host_helpers.cli_factory import CLIFactory
from robottelo.host_helpers.ui_factory import UIFactory
from robottelo.logging import logger
from robottelo.utils.installer import InstallerCommand
from robottelo.utils.manifest import clone


class EnablePluginsSatellite:
    """Miscellaneous settings helper methods"""

    def enable_puppet_satellite(self):
        self.register_to_cdn()
        enable_satellite_cmd = InstallerCommand(
            installer_args=PUPPET_SATELLITE_INSTALLER,
            installer_opts=PUPPET_COMMON_INSTALLER_OPTS,
        )
        result = self.execute(enable_satellite_cmd.get_command(), timeout='20m')
        assert result.status == 0
        assert 'Success!' in result.stdout
        return self

    def enable_multicv_setting(self):
        """Makes multi-CV setting available in the downstream Satellite"""
        cfg_file = 'upstream_only_settings.rb'
        cfg_path = self.execute(f'find /usr/share/gems/gems/ -name {cfg_file}').stdout.strip()
        assert cfg_file in cfg_path, 'Config file not found'
        self.execute(
            f'sed -i "s/allow_multiple_content_views/#allow_multiple_content_views/g" {cfg_path}'
        )
        self.cli.Service.restart()
        assert len(
            self.api.Setting().search(query={'search': f'name={"allow_multiple_content_views"}'})
        ), 'Multi-CV enablement failed'


class ContentInfo:
    """Miscellaneous content helper methods"""

    def get_repo_files(self, repo_path, extension='rpm'):
        """Returns a list of repo files (for example rpms) in specific repository
        directory.

        :param str repo_path: unix path to the repo, e.g. '/var/lib/pulp/fooRepo/'
        :param str extension: extension of searched files. Defaults to 'rpm'
        :param str optional hostname: hostname or IP address of the remote host. If
            ``None`` the hostname will be get from ``main.server.hostname`` config.
        :return: list representing rpm package names
        :rtype: list
        """
        if not repo_path.endswith('/'):
            repo_path += '/'
        result = self.execute(
            f"find {repo_path} -name '*.{extension}' | awk -F/ '{{print $NF}}'",
        )
        if result.status != 0:
            raise CLIReturnCodeError(result.status, result.stderr, f'No .{extension} found')
        # strip empty lines and sort alphabetically (as order may be wrong because
        # of different paths)
        return sorted(repo_file for repo_file in result.stdout.splitlines() if repo_file)

    def get_repo_files_by_url(self, url, extension='rpm'):
        """Returns a list of repo files (for example rpms) in a specific repository
        published at some url.
        :param url: url where the repo or CV is published
        :param extension: extension of searched files. Defaults to 'rpm'
        :return:  list representing rpm package names
        """
        if not url.endswith('/'):
            url += '/'

        result = requests.get(url, verify=False)
        if result.status_code != 200:
            raise requests.HTTPError(f'{url} is not accessible')

        links = re.findall(r'(?<=href=").*?(?=">)', result.text)

        if 'Packages/' not in links:
            return sorted(line for line in links if extension in line)

        files = []
        subs = self.get_repo_files_by_url(f'{url}Packages/', extension='/')
        for sub in subs:
            files.extend(self.get_repo_files_by_url(f'{url}Packages/{sub}', extension))

        return sorted(files)

    def get_repomd(self, repo_url):
        """Fetches content of the repomd file of a repository

        :param repo_url: the 'Published_At' link of a repo
        :return: string with repomd content
        """
        repomd_path = 'repodata/repomd.xml'
        result = requests.get(f'{repo_url}/{repomd_path}', verify=False)
        if result.status_code != 200:
            raise requests.HTTPError(f'{repo_url}/{repomd_path} is not accessible')

        return result.text

    def get_repomd_revision(self, repo_url):
        """Fetches a revision of a repository.

        :param str repo_url: the 'Published_At' link of a repo
        :return: string containing repository revision
        :rtype: str
        """
        match = re.search('(?<=<revision>).*?(?=</revision>)', self.get_repomd(repo_url))
        if not match:
            raise ValueError(f'<revision> not found in repomd file of {repo_url}')

        return match.group(0)

    def checksum_by_url(self, url, sum_type='md5sum'):
        """Returns desired checksum of a file, accessible via URL. Useful when you want
        to calculate checksum but don't want to deal with storing a file and
        removing it afterwards.

        :param str url: URL of a file.
        :param str sum_type: Checksum type like md5sum, sha256sum, sha512sum, etc.
            Defaults to md5sum.
        :return str: string containing the checksum.
        :raises: AssertionError: If non-zero return code received (file couldn't be
            reached or calculation was not successful).
        """
        filename = url.split('/')[-1]
        result = self.execute(f'wget -q --spider {url}')
        if result.status != 0:
            raise AssertionError(f'Failed to get `{filename}` from `{url}`.')
        return self.execute(
            f'wget -qO - {url} | tee {filename} | {sum_type} | awk \'{{print $1}}\''
        ).stdout.strip()

    def upload_manifest(self, org_id, manifest=None, interface='API', timeout=None):
        """Upload a manifest using the requested interface.

        :type org_id: int
        :type manifest: Manifester object or None
        :type interface: str
        :type timeout: int

        :return: the manifest upload result

        """
        if not isinstance(manifest, bytes | io.BytesIO) and (
            not hasattr(manifest, 'content') or manifest.content is None
        ):
            manifest = clone()
        if timeout is None:
            # Set the timeout to 1500 seconds to align with the API timeout.
            timeout = 1500000
        if interface == 'CLI':
            if hasattr(manifest, 'path'):
                self.put(f'{manifest.path}', f'{manifest.name}')
                result = self.cli.Subscription.upload(
                    {'file': manifest.name, 'organization-id': org_id}, timeout=timeout
                )
            else:
                self.put(manifest, manifest.filename)
                result = self.cli.Subscription.upload(
                    {'file': manifest.filename, 'organization-id': org_id}, timeout=timeout
                )
        else:
            if not isinstance(manifest, bytes | io.BytesIO):
                manifest = manifest.content
            result = self.api.Subscription().upload(
                data={'organization_id': org_id}, files={'content': manifest}
            )
        return result

    def is_sca_mode_enabled(self, org_id):
        """This method checks whether Simple Content Access (SCA) mode is enabled for a
        given organization.

        :param str org_id: The unique identifier of the organization to check for SCA mode.
        :return: A boolean value indicating whether SCA mode is enabled or not.
        :rtype: bool
        """
        return self.api.Organization(id=org_id).read().simple_content_access

    def publish_content_view(self, org, repo_list):
        """This method publishes the content view for a given organization and repository list.

        :param str org: The name of the organization to which the content view belongs
        :param list or str repo_list:  A list of repositories or a single repository

        :return: A dictionary containing the details of the published content view.
        """
        repo = repo_list if isinstance(repo_list, list) else [repo_list]
        content_view = self.api.ContentView(organization=org, repository=repo).create()
        content_view.publish()
        return content_view.read()

    def move_pulp_archive(self, org, export_message):
        """
        Moves exported archive(s) and its metadata into import directory,
        sets ownership, returns import path
        """
        self.execute(
            f'rm -rf {PULP_IMPORT_DIR}/{org.name} &&'
            f'mv {PULP_EXPORT_DIR}/{org.name} {PULP_IMPORT_DIR} && '
            f'chown -R pulp:pulp {PULP_IMPORT_DIR}'
        )

        # removes everything before export path,
        # replaces EXPORT_PATH by IMPORT_PATH,
        # removes metadata filename
        return os.path.dirname(re.sub(rf'.*{PULP_EXPORT_DIR}', PULP_IMPORT_DIR, export_message))


class SystemInfo:
    """Things that needs access to satellite shell for gaining satellite system configuration"""

    @property
    def available_capsule_port(self):
        """returns a list of unused ports dedicated for fake capsules on satellite.

        This calls an ss command on the server prompting for a port range. ss
        returns a list of ports which have a PID assigned (a list of ports
        which are already used). This function then substracts unavailable ports
        from the other ones and returns one of available ones randomly.

        :param port_pool: A list of ports used for fake capsules (for RHEL7+: don't
            forget to set a correct selinux context before otherwise you'll get
            Connection Refused error)

        :return: Random available port from interval <9091, 9190>.
        :rtype: int
        """
        port_pool_range = settings.fake_capsules.port_range
        if isinstance(port_pool_range, str):
            port_pool_range = tuple(port_pool_range.split('-'))
        if isinstance(port_pool_range, tuple) and len(port_pool_range) == 2:
            port_pool = range(int(port_pool_range[0]), int(port_pool_range[1]))
        else:
            raise TypeError(
                'Expected type of port_range is a tuple of 2 elements,'
                f'got {type(port_pool_range)} instead'
            )
        # returns a list of strings
        ss_cmd = self.execute(
            f"ss -tnaH sport ge {port_pool[0]} sport le {port_pool[-1]}"
            " | awk '{n=split($4, p, \":\"); print p[n]}' | sort -u"
        )
        if ss_cmd.stderr:
            raise CapsuleTunnelError(
                f'Failed to create ssh tunnel: Error getting port status: {ss_cmd.stderr}'
            )
        # converts a List of strings to a List of integers
        try:
            print(ss_cmd)
            used_ports = map(
                int, [val for val in ss_cmd.stdout.splitlines()[:-1] if val != 'Cannot stat file ']
            )

        except ValueError:
            raise CapsuleTunnelError(
                f'Failed parsing the port numbers from stdout: {ss_cmd.stdout.splitlines()[:-1]}'
            ) from None
        try:
            # take the list of available ports and return randomly selected one
            return random.choice([port for port in port_pool if port not in used_ports])
        except IndexError:
            raise CapsuleTunnelError(
                'Failed to create ssh tunnel: No more ports available for mapping'
            ) from None

    @contextlib.contextmanager
    def default_url_on_new_port(self, oldport, newport):
        """Creates context where the default capsule is forwarded on a new port

        :param int oldport: Port to be forwarded.
        :param int newport: New port to be used to forward `oldport`.

        :return: A string containing the new capsule URL with port.
        :rtype: str

        """

        def check_ncat_startup(pre_ncat_procs):
            post_ncat_procs = self.execute('pgrep ncat').stdout.splitlines()
            ncat_pid = set(post_ncat_procs).difference(set(pre_ncat_procs))
            if len(ncat_pid):
                return ncat_pid

            return None

        def start_ncat():
            pre_ncat_procs = self.execute('pgrep ncat').stdout.splitlines()
            with self.session.shell() as channel:
                # if ncat isn't backgrounded, it prevents the channel from closing
                command = f'ncat -kl -p {newport} -c "ncat {self.hostname} {oldport}" &'
                logger.debug(f'Creating tunnel: {command}')
                channel.send(command)

                try:
                    return wait_for(
                        check_ncat_startup,
                        func_args=[pre_ncat_procs],
                        fail_condition=None,
                        timeout=5,
                        delay=0.5,
                    )[0]
                except TimedOutError as e:
                    err = channel.get_exit_signal()
                    logger.debug(f'Tunnel failed: {err}')
                    # Something failed, so raise an exception.
                    raise CapsuleTunnelError(f'Starting ncat failed: {err}') from e

        ncat_pid = start_ncat()
        try:
            forward_url = f'https://{self.hostname}:{newport}'
            logger.debug(f'Yielding capsule forward port url: {forward_url}')
            yield forward_url
        finally:
            logger.debug(f'Killing ncat pid: {ncat_pid}')
            self.execute(f'kill {ncat_pid.pop()}')

    def validate_pulp_filepath(
        self,
        org,
        dir_path,
        file_names=('*.json', '*.tar.gz'),
    ):
        """Checks the existence of certain files in a pulp dir"""
        extension_query = ' -o '.join([f'-name "{file}"' for file in file_names])
        result = self.execute(rf'find {dir_path}{org.name} -type f \( {extension_query} \)')
        return result.stdout


class ProvisioningSetup:
    """Provisioning tests setup helper methods"""

    def configure_libvirt_cr(self, server_fqdn=settings.libvirt.libvirt_hostname):
        """Configures Libvirt ComputeResource to communicate with Satellite

        :param server_fqdn: Libvirt server FQDN
        :return: None
        """
        # Geneate SSH key-pair for foreman user and copy public key to libvirt server
        self.execute('sudo -u foreman ssh-keygen -q -t rsa -f ~foreman/.ssh/id_rsa -N "" <<< y')
        self.execute(f'ssh-keyscan -t ecdsa {server_fqdn} >> ~foreman/.ssh/known_hosts')
        self.execute(
            f'sshpass -p {settings.server.ssh_password} ssh-copy-id -o StrictHostKeyChecking=no '
            f'-i ~foreman/.ssh/id_rsa root@{server_fqdn}'
        )
        # Install libvirt-client, and verify foreman user is able to communicate with Libvirt server
        self.register_to_cdn()
        self.execute('dnf -y --disableplugin=foreman-protector install libvirt-client')
        assert (
            self.execute(
                f'su foreman -s /bin/bash -c "virsh -c qemu+ssh://root@{server_fqdn}/system list"'
            ).status
            == 0
        )

    def provisioning_cleanup(self, hostname, interface='API'):
        if interface == 'CLI':
            if self.cli.Host.exists(search=('name', hostname)):
                self.cli.Host.delete({'name': hostname})
            assert not self.cli.Host.exists(search=('name', hostname))
        else:
            host = self.api.Host().search(query={'search': f'name="{hostname}"'})
            if host:
                host[0].delete()
            assert not self.api.Host().search(query={'search': f'name={hostname}'})
        # Workaround BZ: 2207698
        assert self.cli.Service.restart().status == 0


class Factories:
    """Mixin that provides attributes for each factory type"""

    @property
    def cli_factory(self):
        if not getattr(self, '_cli_factory', None):
            self._cli_factory = CLIFactory(self)
        return self._cli_factory

    @property
    def api_factory(self):
        if not getattr(self, '_api_factory', None):
            self._api_factory = APIFactory(self)
        return self._api_factory

    @lru_cache
    def ui_factory(self, session):
        return UIFactory(self, session=session)
