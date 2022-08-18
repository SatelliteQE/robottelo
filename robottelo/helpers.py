"""Several helper methods and functions."""
import re
from urllib.parse import urljoin  # noqa

import requests
from nailgun.config import ServerConfig

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError
from robottelo.config import get_credentials
from robottelo.config import get_url
from robottelo.config import settings
from robottelo.constants import PULP_PUBLISHED_YUM_REPOS_PATH
from robottelo.errors import ProvisioningCheckError


def get_nailgun_config(user=None):
    """Return a NailGun configuration file constructed from default values.

    :param user: The ```nailgun.entities.User``` object of an user with additional passwd
        property/attribute

    :return: ``nailgun.config.ServerConfig`` object, populated from user parameter object else
        with values from ``robottelo.config.settings``

    """
    creds = (user.login, user.passwd) if user else get_credentials()
    return ServerConfig(get_url(), creds, verify=False)


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
        if result.status == 0 and updatefile in result.stdout:
            result = ssh.command(
                f'mv -f {updatefile_path} {updatefile_path}.bak', hostname=hostname
            )
            if result.status != 0:
                raise CLIReturnCodeError(
                    result.status,
                    result.stderr,
                    f'Unable to backup existing {updatefile}',
                )
        result = ssh.command(f'wget -O {updatefile_path} {updateinfo_url}', hostname=hostname)
        if result.status != 0:
            raise CLIReturnCodeError(
                result.status, result.stderr, f'Unable to download {updateinfo_url}'
            )

    result = ssh.command(f'modifyrepo {updatefile_path} {repo_path}/repodata/')

    return result


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
    if result.status != 0:
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
            elif curr_val := self.opts.get(key):  # noqa: E203
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
            if opt := opt.strip().split():  # noqa: E203
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
