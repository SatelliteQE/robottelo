"""Module that gather several informations about host"""
import functools
import logging
import os
import re

from packaging.version import Version

from robottelo import ssh
from robottelo.cli.base import CLIReturnCodeError

LOGGER = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def get_host_os_version():
    """Fetches host's OS version through SSH
    :return: str with version
    """
    cmd = ssh.command('cat /etc/redhat-release')
    if cmd.stdout:
        version_description = cmd.stdout[0]
        version_re = r'Red Hat Enterprise Linux Server release (?P<version>\d(\.\d)*)'
        result = re.search(version_re, version_description)
        if result:
            host_os_version = 'RHEL{}'.format(result.group('version'))
            LOGGER.debug('Host version: {}'.format(host_os_version))
            return host_os_version

    LOGGER.warning('Host version not available: {!r}'.format(cmd))
    return 'Not Available'


_SAT_6_VERSION_COMMAND = 'rpm -q satellite'


@functools.lru_cache(maxsize=1)
def get_host_sat_version():
    """Fetches host's Satellite version through SSH
    :return: Satellite version
    :rtype: version
    """
    version, ssh_result = _extract_sat_version(_SAT_6_VERSION_COMMAND)
    if version != 'Not Available':
        LOGGER.debug('Host Satellite version: {}'.format(version))
        return version
    LOGGER.warning('Host Satellite version not available: {!r}'.format(ssh_result))
    return version


def _extract_sat_version(ssh_cmd):
    """Extracts Satellite version if possible or 'Not Available' otherwise

    :param ssh_cmd: str ssh command
    :return: Satellite version
    :rtype: str
    """
    ssh_result = ssh.command(ssh_cmd)
    if ssh_result.stdout:
        version_description = ssh_result.stdout[0]
        version_re = r'[^\d]*(?P<version>\d(\.\d){2})'
        result = re.search(version_re, version_description)
        if result:
            host_sat_version = result.group('version')
            return host_sat_version, ssh_result

    return 'Not Available', ssh_result


def get_repo_files(repo_path, extension='rpm', hostname=None):
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
    result = ssh.command(
        "find {} -name '*.{}' | awk -F/ '{{print $NF}}'".format(repo_path, extension),
        hostname=hostname,
    )
    if result.return_code != 0:
        raise CLIReturnCodeError(
            result.return_code, result.stderr, 'No .{} found'.format(extension)
        )
    # strip empty lines and sort alphabetically (as order may be wrong because
    # of different paths)
    return sorted([repo_file for repo_file in result.stdout if repo_file])


def get_repomd_revision(repo_path, hostname=None):
    """Fetches a revision of repository.

    :param str repo_path: unix path to the repo, e.g. '/var/lib/pulp/fooRepo'
    :param str optional hostname: hostname or IP address of the remote host. If
        ``None`` the hostname will be get from ``main.server.hostname`` config.
    :return: string containing repository revision
    :rtype: str
    """
    repomd_path = 'repodata/repomd.xml'
    result = ssh.command(
        "grep -oP '(?<=<revision>).*?(?=</revision>)' {}/{}".format(repo_path, repomd_path),
        hostname=hostname,
    )
    # strip empty lines
    stdout = [line for line in result.stdout if line]
    if result.return_code != 0 or len(stdout) != 1:
        raise CLIReturnCodeError(
            result.return_code,
            result.stderr,
            'Unable to fetch revision for {}. Please double check your '
            'hostname, path and contents of repomd.xml'.format(repo_path),
        )
    return stdout[0]


class SatVersionDependentValues(object):
    """Class which return values depending on Satellite host version"""

    def __init__(self, *dcts, **kwargs):
        """
        Hold values for different Satellite versions.
        Each value of ``dcts`` must be a dictionary with form {version:dict}
        :param dcts: dct
        """
        self._common = kwargs.get('common', {})
        self._versioned_values = {}
        for dct in dcts:
            self._versioned_values.update(dct)

    def __getitem__(self, item):
        """
        Return value dependent on Satellite version
        :param item: str
        :return: respective Satellite version values
        """

        sat_version = get_host_sat_version()
        try:
            return self._versioned_values[sat_version][item]
        except KeyError:
            return self._common[item]


def get_sat_version():
    """Try to read sat_version from envvar SATELLITE_VERSION
    if not available fallback to ssh connection to get it."""
    sat_ver = os.environ.get('SATELLITE_VERSION') or get_host_sat_version()
    return Version('9999' if 'nightly' in sat_ver else sat_ver)
