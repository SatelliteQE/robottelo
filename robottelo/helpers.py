# -*- encoding: utf-8 -*-
"""Several helper methods and functions."""
import logging
from random import randint
from urlparse import urljoin, urlunsplit

import os
import re
from os.path import join

from fauxfactory import gen_string, gen_integer

from nailgun import entities, entity_mixins

from nailgun.config import ServerConfig

from robottelo import ssh
from robottelo.config import conf
from robottelo.constants import VALID_GPG_KEY_FILE
from robottelo.decorators import bz_bug_is_open

LOGGER = logging.getLogger(__name__)


class DataFileError(Exception):
    """Indicates any issue when reading a data file."""


class HostInfoError(Exception):
    """Indicates any issue when getting host info."""


class InvalidArgumentError(Exception):
    """Indicates an error when an invalid argument is received."""


def get_server_credentials():
    """Return credentials for interacting with a Foreman deployment API.

    :return: A username-password pair.
    :rtype: tuple

    """
    return (
        conf.properties['foreman.admin.username'],
        conf.properties['foreman.admin.password']
    )


def get_server_software():
    """Figure out which product distribution is installed on the server.

    :return: Either 'upstream' or 'downstream'.
    :rtype: str

    """
    return_code = ssh.command(
        '[ -f /usr/share/foreman/lib/satellite/version.rb ]'
    ).return_code
    return 'downstream' if return_code == 0 else 'upstream'


def get_server_url():
    """Return the base URL of the Foreman deployment being tested.

    The following values from the config file are used to build the URL:

    * ``main.server.scheme`` (default: https)
    * ``main.server.hostname`` (required)
    * ``main.server.port`` (default: none)

    Setting ``port`` to 80 does *not* imply that ``scheme`` is 'https'. If
    ``port`` is 80 and ``scheme`` is unset, ``scheme`` will still default to
    'https'.

    :return: A URL.
    :rtype: str

    """
    # If the config file contains an unset property (e.g. `server.scheme=`),
    # then `conf.properties['main.server.scheme']` will return an empty string.
    # If the config file is missing a property, then fetching that property
    # will throw a KeyError exception. Let's deal with both cases by getting a
    # default value of ''.
    scheme = conf.properties.get('main.server.scheme', '')
    hostname = conf.properties['main.server.hostname']
    port = conf.properties.get('main.server.port', '')

    # As promised in the docstring, we must provide a default scheme.
    if scheme == '':
        scheme = 'https'

    # All anticipated error cases have been handled at this point.
    if port == '':
        return urlunsplit((scheme, hostname, '', '', ''))
    else:
        return urlunsplit((
            scheme, '{0}:{1}'.format(hostname, port), '', '', ''
        ))


def get_server_pub_url():
    """Return the pub URL of the server being tested.

    The following values from the config file are used to build the URL:

    * ``main.server.hostname`` (required)

    :return: The pub directory URL.
    :rtype: str

    """
    return urlunsplit(
        ('http', conf.properties['main.server.hostname'], 'pub/', '', '')
    )


def get_server_cert_rpm_url():
    """Return the Katello cert RPM URL of the server being tested.

    The following values from the config file are used to build the URL:

    * ``main.server.hostname`` (required)

    :return: The Katello cert RPM URL.
    :rtype: str

    """
    return urljoin(
        get_server_pub_url(), 'katello-ca-consumer-latest.noarch.rpm')


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
        from :data:`robottelo.config.conf`.

    """
    return ServerConfig(
        get_server_url(),
        get_server_credentials(),
        verify=False,
    )


def get_internal_docker_url():
    """Use the unix socket connection to the local docker daemon. Make sure
    that your Satellite server's docker is configured to allow foreman user
    accessing it. This can be done by::

        $ groupadd docker
        $ usermod -aG docker foreman
        # Add -G docker to the options for the docker daemon
        $ systemctl restart docker
        $ katello-service restart

    """
    return 'unix:///var/run/docker.sock'


def get_external_docker_url():
    """Returns the docker external server url config"""
    external_url = conf.properties.get('docker.external_url')
    if external_url is not None:
        external_url = external_url.format(
            server_hostname=conf.properties['main.server.hostname'])
    return external_url


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
    """List of valid data for input testing.

    Note:
    Although this helper is widely used for different attributes for several
    entities, the following are known behaviors and are handled specifically in
    the corresponding test modules::

        Org - name max length is 242
        Loc - name max length is 246

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


def valid_labels_list():
    """List of valid labels for input testing."""
    return [
        gen_string('alphanumeric', randint(1, 255)),
        gen_string('alpha', randint(1, 255)),
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


def invalid_values_list(interface=None):
    """List of invalid values for input testing.

    This returns invalid values from invalid_names_list() and some interface
    (api/cli/ui) specific empty string values.

    :param str interface: Interface name (one of api/cli/ui).
    :return: Returns the invalid values list
    :rtype: list
    :raises: :meth:`InvalidArgumentError`: If an invalid interface is received.

    """
    if interface not in ['api', 'cli', 'ui', None]:
        raise InvalidArgumentError(
            'Valid interface values are {0}'.format('api, cli, ui only')
        )
    if interface == 'ui':
        return ['', ' '] + invalid_names_list()
    else:  # interface = api or cli or None
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


def configure_entities():
    """Configure NailGun's entity classes.

    Do the following:

    * Set ``entity_mixins.CREATE_MISSING`` to ``True``. This causes method
      ``EntityCreateMixin.create_raw`` to generate values for empty and
      required fields.
    * Set ``nailgun.entity_mixins.DEFAULT_SERVER_CONFIG`` to whatever is
      returned by :meth:`robottelo.helpers.get_nailgun_config`. See
      ``robottelo.entity_mixins.Entity`` for more information on the effects of
      this.
    * Set a default value for ``nailgun.entities.GPGKey.content``.
    * Set the default value for ``nailgun.entities.DockerComputeResource.url``
      if either ``docker.internal_url`` or ``docker.external_url`` is set in
      the configuration file.

    Emit a warning and do not set anything if no ``robottelo.properties``
    configuration file is available.

    """
    entity_mixins.CREATE_MISSING = True
    try:
        entity_mixins.DEFAULT_SERVER_CONFIG = get_nailgun_config()
    except KeyError:
        LOGGER.warn(
            'No `robottelo.properties` configuration file is present. Class '
            '`nailgun.entity_mixins.Entity` (and, therefore, its subclasses) '
            'will not be given a default NailGun server configuration. You '
            'can go ahead and use the entity classes anyway if you pass in a '
            '`server_config` each time you instantiate an entity, you set '
            '`nailgun.entity_mixins.DEFAULT_SERVER_CONFIG`, or you create a '
            'NailGun configuration profile labeled "default".'
        )

    gpgkey_init = entities.GPGKey.__init__

    def patched_gpgkey_init(self, server_config=None, **kwargs):
        """Set a default value on the ``content`` field."""
        gpgkey_init(self, server_config, **kwargs)
        self._fields['content'].default = read_data_file(VALID_GPG_KEY_FILE)
    entities.GPGKey.__init__ = patched_gpgkey_init

    # NailGun provides a default value for ComputeResource.url. We override
    # that value if `docker.internal_url` or `docker.external_url` is set.
    docker_url = None
    if conf.properties.get('docker.internal_url', '') != '':
        docker_url = get_internal_docker_url()
    elif conf.properties.get('docker.external_url', '') != '':
        docker_url = get_external_docker_url()
    if docker_url is not None:
        dockercr_init = entities.DockerComputeResource.__init__

        def patched_dockercr_init(self, server_config=None, **kwargs):
            """Set a default value on the ``docker_url`` field."""
            dockercr_init(self, server_config, **kwargs)
            self._fields['url'].default = docker_url
        entities.DockerComputeResource.__init__ = patched_dockercr_init


def prepare_import_data(tar_path=None):
    """Fetch and uncompress the CSV files from the source."""
    tmpdir = ssh.command('mktemp -d').stdout[0]
    # if path to tar file not specified, download the default one
    if tar_path is None:
        tar_remote_path = conf.properties['transitions.export_tar.url']
        cmd = u'wget {0} -O - | tar -xzvC {1}'.format(tar_remote_path, tmpdir)
    else:
        cmd = u'tar -xzvf {0} -C {1}'.format(tar_path, tmpdir)

    files = {}
    for filename in ssh.command(cmd).stdout:
        for key in ('activation-keys', 'channels', 'config-files-latest',
                    'kickstart-scripts', 'repositories', 'system-groups',
                    'system-profiles', 'users'):
            if filename.endswith(key + '.csv'):
                files[key] = join(tmpdir, filename)
                break
    return tmpdir, files
