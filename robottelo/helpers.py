# -*- encoding: utf-8 -*-
"""Several helper methods and functions."""
import logging
from random import randint

import os
import re
from os.path import join

from fauxfactory import gen_string, gen_integer

from nailgun.config import ServerConfig

from robottelo import ssh
from robottelo.config import settings
from robottelo.decorators import bz_bug_is_open

LOGGER = logging.getLogger(__name__)


class DataFileError(Exception):
    """Indicates any issue when reading a data file."""


class HostInfoError(Exception):
    """Indicates any issue when getting host info."""


def get_server_software():
    """Figure out which product distribution is installed on the server.

    :return: Either 'upstream' or 'downstream'.
    :rtype: str

    """
    return_code = ssh.command(
        '[ -f /usr/share/foreman/lib/satellite/version.rb ]'
    ).return_code
    return 'downstream' if return_code == 0 else 'upstream'


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
        from :data:`robottelo.config.settings`.

    """
    return ServerConfig(
        settings.server.get_url(),
        settings.server.get_credentials(),
        verify=False,
    )


def valid_names_list():
    """
    List of valid names for input testing.
    """
    return [
        gen_string('utf8', 5),
        gen_string('utf8', 255),
        u"{0}-{1}".format(gen_string('utf8', 4), gen_string('utf8', 4)),
        u"{0}.{1}".format(gen_string('utf8', 4), gen_string('utf8', 4)),
        u"նոր օգտվող-{0}".format(gen_string('utf8', 2)),
        u"新用戶-{0}".format(gen_string('utf8', 2)),
        u"नए उपयोगकर्ता-{0}".format(gen_string('utf8', 2)),
        u"нового пользователя-{0}".format(gen_string('utf8', 2)),
        u"uusi käyttäjä-{0}".format(gen_string('utf8', 2)),
        u"νέος χρήστης-{0}".format(gen_string('utf8', 2)),
        u"foo@!#$^&*( ) {0}".format(gen_string('utf8')),
        u"<blink>{0}</blink>".format(gen_string('utf8')),
        u"bar+{{}}|\"?hi {0}".format(gen_string('utf8')),
        u' {0}'.format(gen_string('utf8')),
        u'{0} '.format(gen_string('utf8')),
    ]


def valid_data_list():
    """
    List of valid data for input testing.
    """
    return [
        gen_string('alphanumeric', randint(1, 255)),
        gen_string('alpha', randint(1, 255)),
        gen_string('cjk', randint(1, 85)),
        gen_string('latin1', randint(1, 255)),
        gen_string('numeric', randint(1, 255)),
        gen_string('utf8', randint(1, 85)),
        gen_string('html', randint(1, 85)),
    ]


def invalid_names_list():
    """
    List of invalid names for input testing.
    """
    return [
        gen_string('alphanumeric', 300),
        gen_string('alpha', 300),
        gen_string('cjk', 300),
        gen_string('latin1', 300),
        gen_string('numeric', 300),
        gen_string('utf8', 300),
        gen_string('html', 300),
    ]


def invalid_values_list():
    """List of invalid values for input testing which consists from invalid names
    and few empty string examples. That method should be useful for CLI and API
    tests primarily as we can pass such parameters to a server, but not in UI.
    As we do not verify error messages, it is recommended to use current method
    instead 'invalid_names_list' to have better coverage and prevent redundant
    code.

    """
    return ['', ' ', '\t'] + invalid_names_list()


def generate_strings_list(len1=None, remove_str=None, bug_id=None):
    """Generates a list of all the input strings.

    :param int len1: Specifies the length of the strings to be
        be generated. If the len1 is None then the list is
        returned with string types of random length.
    :returns: A list of various string types.

    """
    if len1 is None:
        len1 = gen_integer(3, 30)
    strings = {
        str_type: gen_string(str_type, len1)
        for str_type
        in (u'alpha', u'numeric', u'alphanumeric',
            u'latin1', u'utf8', u'cjk', u'html')
    }
    # Handle No bug_id, If some entity doesn't support a str_type.
    # Remove str_type from dictionary only if bug is open.
    if remove_str and (bug_id is None or bz_bug_is_open(bug_id)):
        del strings[remove_str]
    return list(strings.values())


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


def prepare_import_data(tar_path=None):
    """Fetch and uncompress the CSV files from the source."""
    tmpdir = ssh.command('mktemp -d').stdout[0]
    # if path to tar file not specified, download the default one
    if tar_path is None:
        tar_remote_path = settings.transition.exported_data
        cmd = u'wget {0} -O - | tar -xzvC {1}'.format(tar_remote_path, tmpdir)
    else:
        cmd = u'tar -xzvf {0} -C {1}'.format(tar_path, tmpdir)

    files = {}
    for file in ssh.command(cmd).stdout:
        for key in (
            'activation-keys',
            'channels',
            'config-files-latest',
            'kickstart-scripts',
            'repositories',
            'system-groups',
            'system-profiles',
            'users'
        ):
            if file.endswith(key + '.csv'):
                files[key] = join(tmpdir, file)
                break
    return tmpdir, files
