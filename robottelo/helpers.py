# -*- encoding: utf-8 -*-
"""Several helper methods and functions."""
import logging
import os
import re
import requests

from tempfile import mkstemp
from nailgun.config import ServerConfig
from robottelo import ssh
from robottelo.config import settings

LOGGER = logging.getLogger(__name__)


class DataFileError(Exception):
    """Indicates any issue when reading a data file."""


class HostInfoError(Exception):
    """Indicates any issue when getting host info."""


class InvalidArgumentError(Exception):
    """Indicates an error when an invalid argument is received."""


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
        if not self.file_downloaded:
            self.fd, self.file_path = mkstemp(suffix='.{}'.format(extention))
            fileobj = os.fdopen(self.fd, 'w')
            fileobj.write(requests.get(fileurl).content)
            fileobj.close()
            if os.path.exists(self.file_path):
                self.file_downloaded = True
            else:
                raise DownloadFileError('Failed to download file from Server.')
        return self.file_path

download_server_file = ServerFileDownloader()


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
