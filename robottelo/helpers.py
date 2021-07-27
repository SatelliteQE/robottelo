"""Several helper methods and functions."""
import contextlib
import os
import random
import re
from tempfile import mkstemp
from urllib.parse import urljoin  # noqa

import requests
from nailgun.config import ServerConfig

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.cli.proxy import CapsuleTunnelError
from robottelo.config import get_cert_rpm_url
from robottelo.config import get_credentials
from robottelo.config import get_url
from robottelo.config import settings
from robottelo.constants import PULP_PUBLISHED_YUM_REPOS_PATH
from robottelo.constants import RHEL_6_MAJOR_VERSION
from robottelo.constants import RHEL_7_MAJOR_VERSION
from robottelo.errors import GCECertNotFoundError
from robottelo.logging import logger


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


class ServerFileDownloader:
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
            self.fd, self.file_path = mkstemp(suffix=f'.{extention}')
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
        with open(f'{local_path}{file_name}', 'wb') as fileobj:
            r = requests.get(file_url)
            r.raise_for_status()
            fileobj.write(r.content)
            fileobj.close()
        if not os.path.exists(f"{local_path}{file_name}"):
            raise DownloadFileError(f'Unable to download {file_name}')
    # download on any server.
    else:
        result = ssh.command(f'wget -O {local_path}{file_name} {file_url}', hostname=hostname)
        if result.return_code != 0:
            raise DownloadFileError(f'Unable to download {file_name}')
    return [f'{local_path}{file_name}', file_name]


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
    result = ''.join(
        ssh.command(
            "cat /usr/share/foreman/lib/satellite/version.rb | grep VERSION | awk '{print $3}'"
        ).stdout
    )
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
        raise HostInfoError(f'Not able to cat /etc/redhat-release "{result.stderr}"')
    match = re.match(r'(?P<distro>.+) release (?P<major>\d+)(.(?P<minor>\d+))?', result.stdout[0])
    if match is None:
        raise HostInfoError(f'Not able to parse release string "{result.stdout[0]}"')
    groups = match.groupdict()
    return (
        groups['distro'],
        int(groups['major']),
        groups['minor'] if groups['minor'] is None else int(groups['minor']),
    )


def get_nailgun_config(user=None):
    """Return a NailGun configuration file constructed from default values.

    :param user: The ```nailgun.entities.User``` object of an user with additional passwd
        property/attribute

    :return: ``nailgun.config.ServerConfig`` object, populated from user parameter object else
        with values from ``robottelo.config.settings``

    """
    creds = (user.login, user.passwd) if user else get_credentials()
    return ServerConfig(get_url(), creds, verify=False)


def escape_search(term):
    """Wraps a search term in " and escape term's " and \\ characters"""
    strip_term = term.strip()
    return '"%s"' % strip_term.replace('\\', '\\\\').replace('"', '\\"')


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
    path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_file = os.path.join(path, "tests", "foreman", "data", filename)
    if os.path.isfile(data_file):
        return data_file
    else:
        raise DataFileError(f'Could not locate the data file "{data_file}"')


def read_data_file(filename):
    """
    Read the contents of data file
    """
    absolute_file_path = get_data_file(filename)
    with open(absolute_file_path) as file_contents:
        return file_contents.read()


def install_katello_ca(hostname=None, sat_hostname=None):
    """Downloads and installs katello-ca rpm

    :param str hostname: Hostname or IP address of the remote host. If
     ``None`` the hostname will be get from ``main.server.hostname`` config
    :return: None.
    :raises: AssertionError: If katello-ca wasn't installed.

    """
    if sat_hostname:
        cert_rpm_url = f'http://{sat_hostname}/pub/katello-ca-consumer-latest.noarch.rpm'
    else:
        sat_hostname = settings.server.hostname
        cert_rpm_url = get_cert_rpm_url()
    ssh.command(f'rpm -Uvh {cert_rpm_url}', hostname)
    # Not checking the return_code here, as rpm could be installed before
    # and installation may fail
    result = ssh.command(f'rpm -q katello-ca-consumer-{sat_hostname}', hostname)
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
    ssh.command('yum erase -y $(rpm -qa |grep katello-ca-consumer)', hostname)
    # Checking the return_code here to verify katello-ca rpm is actually
    # not present in the system
    result = ssh.command(f'rpm -q katello-ca-consumer-{settings.server.hostname}', hostname)
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
        result = ssh.command(f'sed -i -e "{command}" /etc/rhsm/rhsm.conf', hostname)
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
        f'wget -qO - {url} | tee {filename} | md5sum | awk \'{{print $1}}\'',
        hostname=hostname,
    )
    if result.return_code != 0:
        raise AssertionError(f'Failed to calculate md5 checksum of {filename}')
    return result.stdout[0]


def add_remote_execution_ssh_key(hostname, key_path=None, proxy_hostname=None, **kwargs):
    """Add remote execution keys to the client

    :param str proxy_hostname: external capsule hostname
    :param str hostname: The client hostname
    :param str key: Path to a key on the satellite server
    :param dict kwargs: directly passed to `ssh.add_authorized_key`
    """

    # get satellite box ssh-key or defaults to foreman-proxy
    key_path = key_path or '~foreman-proxy/.ssh/id_rsa_foreman_proxy.pub'
    # This connection defaults to settings.server
    server_key = ssh.command(
        cmd='cat %s' % key_path, output_format='base', hostname=proxy_hostname
    ).stdout
    # Sometimes stdout contains extra empty string. Skipping it
    if isinstance(server_key, list):
        server_key = server_key[0]

    # add that key to the client using hostname and kwargs for connection
    ssh.add_authorized_key(server_key, hostname=hostname, **kwargs)


def get_available_capsule_port(port_pool=None):
    """returns a list of unused ports dedicated for fake capsules
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
    if port_pool is None:
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
    ss_cmd = ssh.command(
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
        used_ports = map(int, [val for val in ss_cmd.stdout[:-1] if val != 'Cannot stat file '])

    except ValueError:
        raise CapsuleTunnelError(
            f'Failed parsing the port numbers from stdout: {ss_cmd.stdout[:-1]}'
        )
    try:
        # take the list of available ports and return randomly selected one
        return random.choice([port for port in port_pool if port not in used_ports])
    except IndexError:
        raise CapsuleTunnelError('Failed to create ssh tunnel: No more ports available for mapping')


@contextlib.contextmanager
def default_url_on_new_port(oldport, newport):
    """Creates context where the default capsule is forwarded on a new port

    :param int oldport: Port to be forwarded.
    :param int newport: New port to be used to forward `oldport`.

    :return: A string containing the new capsule URL with port.
    :rtype: str

    """
    domain = settings.server.hostname

    with ssh.get_connection() as connection:
        command = f'ncat -kl -p {newport} -c "ncat {domain} {oldport}"'
        logger.debug(f'Creating tunnel: {command}')
        transport = connection.get_transport()
        channel = transport.open_session()
        channel.get_pty()
        channel.exec_command(command)
        # if exit_status appears until command_timeout, throw error
        if channel.exit_status_ready():
            if channel.recv_exit_status() != 0:
                stderr = ''
                while channel.recv_stderr_ready():
                    stderr += channel.recv_stderr(1)
                logger.debug(f'Tunnel failed: {stderr}')
                # Something failed, so raise an exception.
                raise CapsuleTunnelError(stderr)
        yield f'https://{domain}:{newport}'


class Storage:
    """Turns a dict into an attribute based object.

    Example::

        d = {'foo': 'bar'}
        d['foo'] == 'bar'
        storage = Storage(d)
        storage.foo == 'bar'
    """

    def __init__(self, *args, **kwargs):
        """takes a dict or attrs and sets as attrs"""
        super().__init__()
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
    return [result.return_code, result.stdout]


def form_repo_path(org=None, lce=None, cv=None, cvv=None, prod=None, repo=None, capsule=False):
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
    :param bool capsule: whether the repo_path is from a capsule or not
    :return: full unix path to the specific repository
    :rtype: str
    """
    if not all([org, cv, prod, repo]):
        raise ValueError('`org`, `cv`, `prod` and `repo` arguments are required')
    if not any([lce, cvv]):
        raise ValueError('Either `lce` or `cvv` is required')

    if lce and capsule:
        repo_path = f'{org}/{lce}/custom/{prod}/{repo}'
    elif lce:
        repo_path = f'{org}/{lce}/{cv}/custom/{prod}/{repo}'
    elif cvv:
        repo_path = f'{org}/content_views/{cv}/{cvv}/custom/{prod}/{repo}'

    return os.path.join(PULP_PUBLISHED_YUM_REPOS_PATH, repo_path)


def create_repo(name, repo_fetch_url=None, packages=None, wipe_repodata=False, hostname=None):
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
    repo_path = f'{PULP_PUBLISHED_YUM_REPOS_PATH}/{name}'
    result = ssh.command(f'sudo -u apache mkdir -p {repo_path}', hostname=hostname)
    if result.return_code != 0:
        raise CLIReturnCodeError(result.return_code, result.stderr, 'Unable to create repo dir')
    if repo_fetch_url:
        # Add trailing slash if it's not there already
        if not repo_fetch_url.endswith('/'):
            repo_fetch_url += '/'
        for package in packages:
            result = ssh.command(
                f'wget -P {repo_path} {urljoin(repo_fetch_url, package)}',
                hostname=hostname,
            )
            if result.return_code != 0:
                raise CLIReturnCodeError(
                    result.return_code,
                    result.stderr,
                    f'Unable to download package {package}',
                )
    if wipe_repodata:
        result = ssh.command(f'rm -rf {repo_path}/repodata/', hostname=hostname)
        if result.return_code != 0:
            raise CLIReturnCodeError(
                result.return_code, result.stderr, 'Unable to delete repodata folder'
            )
    result = ssh.command(f'createrepo {repo_path}', hostname=hostname)
    if result.return_code != 0:
        raise CLIReturnCodeError(
            result.return_code,
            result.stderr,
            f'Unable to create repository. stderr contains following info:\n{result.stderr}',
        )

    published_url = 'http://{}{}/pulp/repos/{}/'.format(
        settings.server.hostname,
        f':{settings.server.port}' if settings.server.port else '',
        name,
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
    repo_path = f'{PULP_PUBLISHED_YUM_REPOS_PATH}/{name}'
    updatefile_path = f'{repo_path}/{updatefile}'
    if updateinfo_url:
        result = ssh.command(f'find {updatefile_path}', hostname=hostname)
        if result.return_code == 0 and updatefile in result.stdout[0]:
            result = ssh.command(
                f'mv -f {updatefile_path} {updatefile_path}.bak', hostname=hostname
            )
            if result.return_code != 0:
                raise CLIReturnCodeError(
                    result.return_code,
                    result.stderr,
                    f'Unable to backup existing {updatefile}',
                )
        result = ssh.command(f'wget -O {updatefile_path} {updateinfo_url}', hostname=hostname)
        if result.return_code != 0:
            raise CLIReturnCodeError(
                result.return_code, result.stderr, f'Unable to download {updateinfo_url}'
            )

    result = ssh.command(f'modifyrepo {updatefile_path} {repo_path}/repodata/')

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
    token = re.search('"token":"(.*?)"', input)
    if token is None:
        raise IndexError("the given string does not contain any authenticity token references")
    else:
        return token[1]


def get_web_session():
    """Logs in as admin user and returns the valid requests.Session object"""
    sat_session = requests.Session()
    url = f'https://{settings.server.hostname}'

    init_request = sat_session.get(url, verify=False)
    login_request = sat_session.post(
        f'{url}/users/login',
        data={
            'authenticity_token': extract_ui_token(init_request.text),
            'login[login]': settings.server.admin_username,
            'login[password]': settings.server.admin_password,
            'commit': 'Log In',
        },
        verify=False,
    )
    login_request.raise_for_status()
    if 'users/login' in login_request.history[0].headers.get('Location'):
        raise requests.HTTPError('Failed to authenticate using the given credentials')
    return sat_session


def host_provisioning_check(ip_addr):
    """Check the provisioned host status by pinging the ip of host and check
    to connect to ssh port

    :param ip_addr: IP address of the provisioned host
    :return: ssh command return code and stdout
    """
    result = ssh.command(
        f'for i in {{1..60}}; do ping -c1 {ip_addr} && exit 0; sleep 20; done; exit 1'
    )
    if result.return_code != 0:
        raise ProvisioningCheckError(f'Failed to ping virtual machine Error:{result.stdout}')


def slugify_component(string, keep_hyphens=True):
    """Make component name a slug

    Arguments:
        string {str} -- Component name e.g: ActivationKeys
        keep_hyphens {bool} -- Keep hyphens or replace with underscores

    Returns:
        str -- component slug e.g: activationkeys
    """
    string = string.replace(" and ", "&")
    if not keep_hyphens:
        string = string.replace('-', '_')
    return re.sub("[^-_a-zA-Z0-9]", "", string.lower())


# --- Issue based Pytest markers ---


def download_gce_cert():
    ssh.command(f'curl {settings.gce.cert_url} -o {settings.gce.cert_path}')
    if ssh.command(f'[ -f {settings.gce.cert_path} ]').return_code != 0:
        raise GCECertNotFoundError(
            f"The GCE certificate in path {settings.gce.cert_path} is not found in satellite."
        )
    return download_server_file('json', settings.gce.cert_url)


def idgen(val):
    """
    The id generator function which will return string that will append to the parameterized
    test name
    """
    return '_parameter'


class InstallerCommand:
    """This class constructs, parses, updates and gets formatted installer commands"""

    def __init__(self, *args, command='satellite-installer', allow_dupes=False, **kwargs):
        """This allows multiple methods for InstallerClass creation

        InstallerCommand('f', 'verbose', command='satellite-installer', sat_host='my_sat')
        InstallerCommand(installer_args=['f', 'verbose'], sat_host='my_sat')
        InstallerCommand(installer_args=['f', 'verbose'], installer_opts={'sat_host': 'my_sat'})

        :param allow_dupes: Allow duplicate options, doesn't apply to future updates

        """

        self.command = command
        self.args = kwargs.pop('installer_args', [])
        self.opts = kwargs.pop('installer_opts', {})
        self.update(*args, allow_dupes=allow_dupes, **kwargs)

    def get_command(self):
        """Construct the final command in the form of a string"""
        command_str = self.command
        for arg in self.args:
            command_str += f' {"-" if len(arg) == 1 else "--"}{arg}'
        for key, val in self.opts.items():
            # if we have duplicate keys (list of values), add each option/value pair
            if isinstance(val, list):
                for v in val:
                    command_str += f' --{key.replace("_", "-")} {v}'
            else:
                command_str += f' --{key.replace("_", "-")} {val}'
        return command_str

    def update(self, *args, allow_dupes=False, **kwargs):
        """Update one or more arguments and options
        values passed as positional and keyword arguments
        """
        new_args = [arg for arg in args if arg not in self.args]
        self.args.extend(new_args)
        if not allow_dupes:
            self.opts.update(kwargs)
        # iterate over all keyword arguments passed in
        for key, val in kwargs.items():
            # if we won't want duplicate keys, override the current value
            if not allow_dupes:
                self.opts[key] = val
            # if we do want duplicate keys, convert the value to a list
            elif (curr_val := self.opts.get(key)) :  # noqa: E203
                val = [val]
                if not isinstance(curr_val, list):
                    curr_val = [curr_val]
                # and add the old value(s) to the new list
                val += curr_val
            self.opts[key] = val

    @classmethod
    def from_cmd_str(cls, command='satellite-installer', cmd_str=None):
        """Construct the class based on a string representing expected installer options.
        This is mostly used for capsule-certs-generate output parsing.
        """
        installer_command, listening = '', False
        for line in cmd_str.splitlines():
            if line.strip().startswith(command):
                listening = True
            if listening:
                installer_command += ' ' + ' '.join(line.replace('\\', '').split())
        installer_command = installer_command.replace(command, '').strip()
        cmd_args, add_later = {}, []
        for opt in installer_command.split('--'):
            if (opt := opt.strip().split()) :  # noqa: E203
                if opt[0] in cmd_args:
                    add_later.append(opt)
                else:
                    cmd_args[opt[0]] = opt[1]
        installer = cls(command=command, installer_opts=cmd_args)
        for opt in add_later:
            installer.update(allow_dupes=True, **{opt[0]: opt[1]})
        return installer

    def __repr__(self):
        """Custom repr will give the constructed command output"""
        return self.get_command()
