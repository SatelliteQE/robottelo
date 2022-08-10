import contextlib
import random
import re

import requests

from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.proxy import CapsuleTunnelError
from robottelo.config import settings
from robottelo.host_helpers.api_factory import APIFactory
from robottelo.host_helpers.cli_factory import CLIFactory
from robottelo.logging import logger


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

    def md5_by_url(self, url):
        """Returns md5 checksum of a file, accessible via URL. Useful when you want
        to calculate checksum but don't want to deal with storing a file and
        removing it afterwards.

        :param str url: URL of a file.
        :return str: string containing md5 checksum.
        :raises: AssertionError: If non-zero return code received (file couldn't be
            reached or calculation was not successful).
        """
        filename = url.split('/')[-1]
        result = self.execute(f'wget -qO - {url} | tee {filename} | md5sum | awk \'{{print $1}}\'')
        if result.status != 0:
            raise AssertionError(f'Failed to calculate md5 checksum of {filename}')
        return result.stdout


class SystemInfo:
    """Things that needs access to satellite shell for gaining satellite system configuration"""

    @property
    def get_available_capsule_port(self):
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
        if type(port_pool_range) is str:
            port_pool_range = tuple(port_pool_range.split('-'))
        if type(port_pool_range) is tuple and len(port_pool_range) == 2:
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
        if ss_cmd.stderr[1]:
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
            )
        try:
            # take the list of available ports and return randomly selected one
            return random.choice([port for port in port_pool if port not in used_ports])
        except IndexError:
            raise CapsuleTunnelError(
                'Failed to create ssh tunnel: No more ports available for mapping'
            )

    @contextlib.contextmanager
    def default_url_on_new_port(self, oldport, newport):
        """Creates context where the default capsule is forwarded on a new port

        :param int oldport: Port to be forwarded.
        :param int newport: New port to be used to forward `oldport`.

        :return: A string containing the new capsule URL with port.
        :rtype: str

        """
        pre_ncat_procs = self.execute('pgrep ncat').stdout.splitlines()
        with self.session.shell() as channel:
            # if ncat isn't backgrounded, it prevents the channel from closing
            command = f'ncat -kl -p {newport} -c "ncat {self.hostname} {oldport}" &'
            logger.debug(f'Creating tunnel: {command}')
            channel.send(command)
            post_ncat_procs = self.execute('pgrep ncat').stdout.splitlines()
            ncat_pid = set(post_ncat_procs).difference(set(pre_ncat_procs))
            if not len(ncat_pid):
                stderr = channel.get_exit_status()[1]
                logger.debug(f'Tunnel failed: {stderr}')
                # Something failed, so raise an exception.
                raise CapsuleTunnelError(f'Starting ncat failed: {stderr}')
            forward_url = f'https://{self.hostname}:{newport}'
            logger.debug(f'Yielding capsule forward port url: {forward_url}')
            try:
                yield forward_url
            finally:
                logger.debug(f'Killing ncat pid: {ncat_pid}')
                self.execute(f'kill {ncat_pid.pop()}')


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
