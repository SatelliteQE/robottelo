# -*- encoding: utf-8 -*-
"""Several helper methods and functions."""
import contextlib
import logging
import os
import random
import re
import requests

from tempfile import mkstemp
from nailgun.config import ServerConfig
from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.proxy import CapsuleTunnelError
from robottelo.config import settings
from robottelo.constants import (
    PULP_PUBLISHED_YUM_REPOS_PATH,
    RHEL_6_MAJOR_VERSION,
    RHEL_7_MAJOR_VERSION,
)

from urllib.parse import urljoin  # noqa

LOGGER = logging.getLogger(__name__)


class DataFileError(Exception):
    """Indicates any issue when reading a data file."""


class HostInfoError(Exception):
    """Indicates any issue when getting host info."""


class ProvisioningCheckError(Exception):
    """Indicates any issue when provisioning a host."""
    pass


class InvalidArgumentError(Exception):
    """Indicates an error when an invalid argument is received."""


class ProxyError(Exception):
    """Indicates an error in state of proxy"""


class DownloadFileError(Exception):
    """Indicates an error when failure in downloading file from server."""


class ServerFileDownloader(object):
    """Downloads file from given fileurl to local /temp dirctory."""

    def __init__(self):
        self.file_downloaded = False
        self.fd = None
        self.file_path = None

    def __call__(self, extention, fileurl):
        """Downloads file from given fileurl to local /temp directory with
        given extention.

        :param str extention: The file extention with which the file to be
            saved in /temp directory.
        :param str fileurl: The complete server file path from where the
            file will be downloaded.
        :returns: Returns complete file path with name of downloaded file.
        """
        if not self.file_downloaded:  # pragma: no cover
            self.fd, self.file_path = mkstemp(suffix='.{}'.format(extention))
            fileobj = os.fdopen(self.fd, 'wb')
            fileobj.write(requests.get(fileurl).content)
            fileobj.close()
            if os.path.exists(self.file_path):
                self.file_downloaded = True
            else:
                raise DownloadFileError('Failed to download file from Server.')
        return self.file_path


download_server_file = ServerFileDownloader()


def file_downloader(file_url, local_path=None, file_name=None, hostname=None):
    """Downloads file from given fileurl to directory specified by local_path
    with given file_name on host specified by hostname. Leave hostname as None
    to download file on the localhost.If remote directory is not specified it
    downloads file to /tmp/.
    :param str file_url: The complete server file path from where the
        file will be downloaded.
    :param str local_path: Name of directory where file will be saved. If not
    provided file will be saved in /tmp/ directory.
    :param str file_name: Name of the file to be saved with. If not provided filename
    from url will be used.
    :param str hostname: Hostname of server where the file need to be downloaded.
    :returns: Returns list containing complete file path and name of downloaded file.
    """
    if file_name is None:
        _, file_name = os.path.split(file_url)
    if local_path is None:
        local_path = '/tmp/'

    # download on localhost
    if hostname is None:
        with open('{}{}'.format(local_path, file_name), 'wb') as fileobj:
            r = requests.get(file_url)
            r.raise_for_status()
            fileobj.write(r.content)
            fileobj.close()
        if not os.path.exists("{}{}".format(local_path, file_name)):
            raise DownloadFileError('Unable to download {}'.format(file_name))
    # download on any server.
    else:
        result = ssh.command('wget -O {}{} {}'.format(
            local_path, file_name, file_url), hostname=hostname)
        if result.return_code != 0:
            raise DownloadFileError('Unable to download {}'.format(file_name))
    return ['{}{}'.format(local_path, file_name), file_name]


def get_server_software():
    """Figure out which product distribution is installed on the server.

    :return: Either 'upstream' or 'downstream'.
    :rtype: str

    """
    if ssh.command('rpm -q satellite &>/dev/null').return_code == 0:
        return 'downstream'
    return 'upstream'


def get_server_version():
    """Read Satellite version.

    Inspect server /usr/share/foreman/lib/satellite/version.rb in
    order to get the installed Satellite version.

    :return: Either a string containing the Satellite version or
        ``None`` if the version.rb file is not present.
    """
    result = ''.join(ssh.command(
        "cat /usr/share/foreman/lib/satellite/version.rb | grep VERSION | "
        "awk '{print $3}'"
    ).stdout)
    result = result.replace('"', '').strip()
    if len(result) == 0:
        return None
    return result


def get_host_info(hostname=None):
    """Get remote host's distribution information

    :param str hostname: Hostname or IP address of the remote host. If ``None``
        the hostname will be get from ``main.server.hostname`` config.
    :returns: A tuple in the form ``(distro, major, minor)``. ``major`` and
        ``minor`` are integers. ``minor`` can be ``None`` if not available.

    """
    result = ssh.command('cat /etc/redhat-release', hostname)
    if result.return_code != 0:
        raise HostInfoError('Not able to cat /etc/redhat-release "{0}"'.format(
            result.stderr
        ))
    match = re.match(
        r'(?P<distro>.+) release (?P<major>\d+)(.(?P<minor>\d+))?',
        result.stdout[0],
    )
    if match is None:
        raise HostInfoError(
            u'Not able to parse release string "{0}"'.format(result.stdout[0]))
    groups = match.groupdict()
    return (
        groups['distro'],
        int(groups['major']),
        groups['minor'] if groups['minor'] is None else int(groups['minor'])
    )


def get_nailgun_config():
    """Return a NailGun configuration file constructed from default values.

    :return: A ``nailgun.config.ServerConfig`` object, populated with values
        from ``robottelo.config.settings``.

    """
    return ServerConfig(
        settings.server.get_url(),
        settings.server.get_credentials(),
        verify=False,
    )


def escape_search(term):
    """Wraps a search term in " and escape term's " and \\ characters"""
    strip_term = term.strip()
    return u'"%s"' % strip_term.replace('\\', '\\\\').replace('"', '\\"')


def update_dictionary(default, updates):
    """
    Updates default dictionary with elements from
    optional dictionary.

    @param default: A python dictionary containing the minimal
    required arguments to create a CLI object.
    @param updates: A python dictionary containing attributes
    to overwrite on default dictionary.

    @return default: The modified default python dictionary.
    """

    if updates:
        for key in set(default.keys()).intersection(set(updates.keys())):
            default[key] = updates[key]

    return default


def get_data_file(filename):
    """Returns correct path of file from data folder."""
    path = os.path.realpath(
        os.path.join(os.path.dirname(__file__), os.pardir))
    data_file = os.path.join(path, "tests", "foreman", "data", filename)
    if os.path.isfile(data_file):
        return data_file
    else:
        raise DataFileError(
            'Could not locate the data file "{0}"'.format(data_file))


def read_data_file(filename):
    """
    Read the contents of data file
    """
    absolute_file_path = get_data_file(filename)
    with open(absolute_file_path, 'r') as file_contents:
        return file_contents.read()


def install_katello_ca(hostname=None):
    """Downloads and installs katello-ca rpm

    :param str hostname: Hostname or IP address of the remote host. If
     ``None`` the hostname will be get from ``main.server.hostname`` config
    :return: None.
    :raises: AssertionError: If katello-ca wasn't installed.

    """
    ssh.command(
        u'rpm -Uvh {0}'.format(settings.server.get_cert_rpm_url()),
        hostname
    )
    # Not checking the return_code here, as rpm could be installed before
    # and installation may fail
    result = ssh.command(
        u'rpm -q katello-ca-consumer-{0}'
        .format(settings.server.hostname),
        hostname
    )
    # Checking the return_code here to verify katello-ca rpm is actually
    # present in the system
    if result.return_code != 0:
        raise AssertionError('Failed to install the katello-ca rpm')


def remove_katello_ca(hostname=None):
    """Removes katello-ca rpm

    :param str hostname: Hostname or IP address of the remote host. If
     ``None`` the hostname will be get from ``main.server.hostname`` config
    :return: None.
    :raises: AssertionError: If katello-ca wasn't removed.

    """
    # Not checking the return_code here, as rpm can be not even installed
    # and deleting may fail
    ssh.command(
        'yum erase -y $(rpm -qa |grep katello-ca-consumer)',
        hostname
    )
    # Checking the return_code here to verify katello-ca rpm is actually
    # not present in the system
    result = ssh.command(
        'rpm -q katello-ca-consumer-{0}'
        .format(settings.server.hostname),
        hostname
    )
    if result.return_code == 0:
        raise AssertionError('Failed to remove the katello-ca rpm')
    # Resetting rhsm.conf to point to cdn
    rhsm_updates = [
        's/^hostname.*/hostname=subscription.rhn.redhat.com/',
        's|^prefix.*|prefix=/subscription|',
        's|^baseurl.*|baseurl=https://cdn.redhat.com|',
        's/^repo_ca_cert.*/repo_ca_cert=%(ca_cert_dir)sredhat-uep.pem/',
    ]
    for command in rhsm_updates:
        result = ssh.command(
            'sed -i -e "{0}" /etc/rhsm/rhsm.conf'.format(command),
            hostname
        )
        if result.return_code != 0:
            raise AssertionError('Failed to reset the rhsm.conf')


def md5_by_url(url, hostname=None):
    """Returns md5 checksum of a file, accessible via URL. Useful when you want
    to calculate checksum but don't want to deal with storing a file and
    removing it afterwards.

    :param str url: URL of a file.
    :param str hostname: Hostname or IP address of the remote host. If
         ``None`` the hostname will be get from ``main.server.hostname`` config
    :return str: string containing md5 checksum.
    :raises: AssertionError: If non-zero return code received (file couldn't be
        reached or calculation was not successful).
    """
    filename = url.split('/')[-1]
    result = ssh.command(
        'wget -qO - {} | tee {} | md5sum | awk \'{{print $1}}\''.format(
            url, filename),
        hostname=hostname
    )
    if result.return_code != 0:
        raise AssertionError(
            'Failed to calculate md5 checksum of {}'.format(filename))
    return result.stdout[0]


def add_remote_execution_ssh_key(hostname, key_path=None,
                                 proxy_hostname=None, **kwargs):
    """Add remote execution keys to the client

    :param str proxy_hostname: external capsule hostname
    :param str hostname: The client hostname
    :param str key: Path to a key on the satellite server
    :param dict kwargs: directly passed to `ssh.add_authorized_key`
    """

    # get satellite box ssh-key or defaults to foreman-proxy
    key_path = key_path or '~foreman-proxy/.ssh/id_rsa_foreman_proxy.pub'
    # This connection defaults to settings.server
    server_key = ssh.command(cmd='cat %s' % key_path, output_format='plain',
                             hostname=proxy_hostname).stdout
    # Sometimes stdout contains extra empty string. Skipping it
    if isinstance(server_key, list):
        server_key = server_key[0]

    # add that key to the client using hostname and kwargs for connection
    ssh.add_authorized_key(server_key, hostname=hostname, **kwargs)


def get_available_capsule_port(port_pool=None):
    """returns a list of unused ports dedicated for fake capsules
    This calls a fuser command on the server prompting for a port range. fuser
    commands returns a list of ports which have a PID assigned (a list of ports
    which are already used). This function then substracts unavailable ports
    from the other ones and returns one of available ones randomly.

    :param port_pool: A list of ports used for fake capsules (for RHEL7+: don't
        forget to set a correct selinux context before otherwise you'll get
        Connection Refused error)

    :return: Random available port from interval <9091, 9190>.
    :rtype: int
    """
    if port_pool is None:
        port_pool_range = settings.fake_capsules.port_range
        if type(port_pool_range) is tuple and len(port_pool_range) == 2:
            port_pool = range(int(port_pool_range[0]), int(port_pool_range[1]))
        else:
            raise TypeError(
                '''Expected type of port_range is a tuple of 2 elements,
                got {0} instead'''
                .format(type(port_pool_range))
            )
    # returns a list of strings
    fuser_cmd = ssh.command(
        'fuser -n tcp {{{0}..{1}}} 2>&1 | awk -F/ \'{{print$1}}\''
        .format(port_pool[0], port_pool[-1])
    )
    if fuser_cmd.stderr:
        raise CapsuleTunnelError(
            'Failed to create ssh tunnel: Error getting port status: {0}'
            .format(fuser_cmd.stderr)
        )
    # converts a List of strings to a List of integers
    try:
        print(fuser_cmd)
        used_ports = map(
            int,
            [val for val in fuser_cmd.stdout[:-1]
                if val != 'Cannot stat file ']
        )

    except ValueError:
        raise CapsuleTunnelError(
            'Failed parsing the port numbers from stdout: {0}'
            .format(fuser_cmd.stdout[:-1])
        )
    try:
        # take the list of available ports and return randomly selected one
        return random.choice(
            [port for port in port_pool if port not in used_ports]
        )
    except IndexError:
        raise CapsuleTunnelError(
            'Failed to create ssh tunnel: No more ports available for mapping'
        )


@contextlib.contextmanager
def default_url_on_new_port(oldport, newport):
    """Creates context where the default capsule is forwarded on a new port

    :param int oldport: Port to be forwarded.
    :param int newport: New port to be used to forward `oldport`.

    :return: A string containing the new capsule URL with port.
    :rtype: str

    """
    logger = logging.getLogger('robottelo')
    domain = settings.server.hostname

    with ssh.get_connection() as connection:
        command = (
            u'ncat -kl -p {0} -c "ncat {1} {2}"'
        ).format(newport, domain, oldport)
        logger.debug('Creating tunnel: {0}'.format(command))
        transport = connection.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel.exec_command(command)
        # if exit_status appears until command_timeout, throw error
        if channel.exit_status_ready():
            if channel.recv_exit_status() != 0:
                stderr = u''
                while channel.recv_stderr_ready():
                    stderr += channel.recv_stderr(1)
                logger.debug('Tunnel failed: {0}'.format(stderr))
                # Something failed, so raise an exception.
                raise CapsuleTunnelError(stderr)
        yield 'https://{0}:{1}'.format(domain, newport)


class Storage(object):
    """Turns a dict into an attribute based object.

    Example::

        d = {'foo': 'bar'}
        d['foo'] == 'bar'
        storage = Storage(d)
        storage.foo == 'bar'
    """
    def __init__(self, *args, **kwargs):
        """takes a dict or attrs and sets as attrs"""
        super(Storage, self).__init__()
        for item in args:
            kwargs.update(item)
        for key, value in kwargs.items():
            setattr(self, key, value)


def get_func_name(func, test_item=None):
    """Given a func object return standardized name to use across project"""
    names = [func.__module__]
    if test_item:
        func_class = getattr(test_item, 'cls')
    elif hasattr(func, 'im_class'):
        func_class = getattr(func, 'im_class')
    elif hasattr(func, '__self__'):
        func_class = func.__self__.__class__
    else:
        func_class = None
    if func_class:
        names.append(func_class.__name__)

    names.append(func.__name__)
    return '.'.join(names)


def get_services_status():
    """Check if core services are running"""
    major_version = get_host_info()[1]
    services = (
        'foreman-proxy',
        'foreman-tasks',
        'httpd',
        'mongod',
        'postgresql',
        'pulp_celerybeat',
        'pulp_resource_manager',
        'pulp_streamer',
        'pulp_workers',
        'qdrouterd',
        'qpidd',
        'smart_proxy_dynflow_core',
        'squid',
        'tomcat6' if major_version == RHEL_6_MAJOR_VERSION else 'tomcat',
    )

    # check `services` status using service command
    if major_version >= RHEL_7_MAJOR_VERSION:
        status_format = '''(for i in {0}; do systemctl is-active $i -q; rc=$?;
        if [[ $rc != 0 ]]; then systemctl status $i; exit $rc; fi; done);'''
    else:
        status_format = '''(for i in {0}; do service $i status &>/dev/null; rc=$?;
        if [[ $rc != 0 ]]; then service $i status; exit $rc; fi; done);'''

    result = ssh.command(status_format.format(' '.join(services)))
    return[result.return_code, result.stdout]


def form_repo_path(org=None, lce=None, cv=None, cvv=None, prod=None,
                   repo=None):
    """Forms unix path to the directory containing published repository in
    pulp using provided entity names. Supports both repositories in content
    view version and repositories in lifecycle environment. Note that either
    `cvv` or `lce` is required.

    :param str org: organization label
    :param str optional lce: lifecycle environment label
    :param str cv: content view label
    :param str optional cvv: content view version, e.g. '1.0'
    :param str prod: product label
    :param str repo: repository label
    :return: full unix path to the specific repository
    :rtype: str
    """
    if not all([org, cv, prod, repo]):
        raise ValueError(
            '`org`, `cv`, `prod` and `repo` arguments are required')
    if not any([lce, cvv]):
        raise ValueError('Either `lce` or `cvv` is required')

    if lce:
        repo_path = '{}/{}/{}/custom/{}/{}'.format(org, lce, cv, prod, repo)
    elif cvv:
        repo_path = '{}/content_views/{}/{}/custom/{}/{}'.format(
            org, cv, cvv, prod, repo)

    return os.path.join(PULP_PUBLISHED_YUM_REPOS_PATH, repo_path)


def create_repo(name, repo_fetch_url=None, packages=None, wipe_repodata=False,
                hostname=None):
    """Creates a repository from given packages and publishes it into pulp's
    directory for web access.

    :param str name: repository name - name of a directory with packages
    :param str repo_fetch_url: URL to fetch packages from
    :param packages: list of packages to fetch (with extension)
    :param wipe_repodata: whether to recursively delete repodata folder
    :param str optional hostname: hostname or IP address of the remote host. If
        ``None`` the hostname will be get from ``main.server.hostname`` config.
    :return: URL where the repository can be accessed
    :rtype: str
    """
    repo_path = '{}/{}'.format(PULP_PUBLISHED_YUM_REPOS_PATH, name)
    result = ssh.command(
        'sudo -u apache mkdir -p {}'.format(repo_path), hostname=hostname)
    if result.return_code != 0:
        raise CLIReturnCodeError(
            result.return_code, result.stderr, 'Unable to create repo dir')
    if repo_fetch_url:
        # Add trailing slash if it's not there already
        if not repo_fetch_url.endswith('/'):
            repo_fetch_url += '/'
        for package in packages:
            result = ssh.command(
                'wget -P {} {}'
                .format(repo_path, urljoin(repo_fetch_url, package)),
                hostname=hostname,
            )
            if result.return_code != 0:
                raise CLIReturnCodeError(
                    result.return_code,
                    result.stderr,
                    'Unable to download package {}'.format(package),
                )
    if wipe_repodata:
        result = ssh.command(
            'rm -rf {}/{}'.format(repo_path, 'repodata/'),
            hostname=hostname
        )
        if result.return_code != 0:
            raise CLIReturnCodeError(
                result.return_code,
                result.stderr,
                'Unable to delete repodata folder',
            )
    result = ssh.command('createrepo {}'.format(repo_path), hostname=hostname)
    if result.return_code != 0:
        raise CLIReturnCodeError(
            result.return_code,
            result.stderr,
            'Unable to create repository. stderr contains following info:\n{}'
            .format(result.stderr),
        )

    published_url = 'http://{}{}/pulp/repos/{}/'.format(
        settings.server.hostname,
        ':{}'.format(settings.server.port) if settings.server.port else '',
        name
    )

    return published_url


def repo_add_updateinfo(name, updateinfo_url=None, hostname=None):
    """Modify repo with contents of updateinfo.xml file.

    :param str name: repository name
    :param str optional updateinfo_url: URL to download updateinfo.xml file
        from. If not specified - updateinfo.xml from repository folder will be
        used instead
    :param str optional hostname: hostname or IP address of the remote host. If
        ``None`` the hostname will be get from ``main.server.hostname`` config.
    :return: result of executing `modifyrepo` command
    """
    updatefile = 'updateinfo.xml'
    repo_path = '{}/{}'.format(PULP_PUBLISHED_YUM_REPOS_PATH, name)
    updatefile_path = '{}/{}'.format(repo_path, updatefile)
    if updateinfo_url:
        result = ssh.command(
            'find {}'.format(updatefile_path),
            hostname=hostname
        )
        if result.return_code == 0 and updatefile in result.stdout[0]:
            result = ssh.command(
                'mv -f {} {}.bak'.format(updatefile_path, updatefile_path),
                hostname=hostname
            )
            if result.return_code != 0:
                raise CLIReturnCodeError(
                    result.return_code,
                    result.stderr,
                    'Unable to backup existing {}'.format(updatefile),
                )
        result = ssh.command(
            'wget -O {} {}'.format(updatefile_path, updateinfo_url),
            hostname=hostname,
        )
        if result.return_code != 0:
            raise CLIReturnCodeError(
                result.return_code,
                result.stderr,
                'Unable to download {}'.format(updateinfo_url),
            )

    result = ssh.command(
        'modifyrepo {} {}/{}'.format(updatefile_path, repo_path, 'repodata/')
    )

    return result


def extract_capsule_satellite_installer_command(text):
    """Extract satellite installer command from capsule-certs-generate command
    output
    """
    cmd_start_with = 'satellite-installer'
    cmd_lines = []
    if text:
        if isinstance(text, (list, tuple)):
            lines = text
        else:
            lines = text.split('\n')
        cmd_start_found = False
        cmd_end_found = False
        for line in lines:
            if line.lstrip().startswith(cmd_start_with):
                cmd_start_found = True
            if cmd_start_found and not cmd_end_found:
                cmd_lines.append(line.strip('\\'))
                if not line.endswith('\\'):
                    cmd_end_found = True
    if cmd_lines:
        cmd = ' '.join(cmd_lines)
        # remove empty spaces
        while '  ' in cmd:
            cmd = cmd.replace('  ', ' ')
        return cmd
    return None


def extract_ui_token(input):
    """Extracts and returns the CSRF protection token from a given
    HTML string"""
    token = re.search(
        r"authenticity_token\" value=\"[^\"]+",
        input
    )
    if token is None:
        raise IndexError("the given string does not contain any authenticity"
                         "token references")
    else:
        return(token[0].split('value="')[-1])


def get_web_session():
    """Logs in as admin user and returns the valid requests.Session object"""
    sat_session = requests.Session()
    url = 'https://{0}'.format(settings.server.hostname)

    init_request = sat_session.get(
        url,
        verify=False
    )
    login_request = sat_session.post(
        '{0}/users/login'.format(url),
        data={
            'authenticity_token': extract_ui_token(init_request.text),
            'login[login]': settings.server.admin_username,
            'login[password]': settings.server.admin_password,
            'commit': 'Log In'
        },
        verify=False
    )
    login_request.raise_for_status()
    if 'users/login' in login_request.history[0].headers.get('Location'):
        raise requests.HTTPError(
            'Failed to authenticate using the given credentials'
        )
    return(sat_session)


def host_provisioning_check(ip_addr):
    """Check the provisioned host status by pinging the ip of host and check
    to connect to ssh port

    :param ip_addr: IP address of the provisioned host
    :return: ssh command return code and stdout
    """
    result = ssh.command(
        u'for i in {{1..60}}; do ping -c1 {0} && exit 0; sleep 20;'
        u' done; exit 1'.format(ip_addr))
    if result.return_code != 0:
        raise ProvisioningCheckError(
            'Failed to ping virtual machine Error:{0}'.format(
                result.stdout))
