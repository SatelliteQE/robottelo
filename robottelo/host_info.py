"""Module that gather several informations about host"""
import logging

import re
from cachetools import lru_cache

from robottelo import ssh
LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_host_os_version():
    """Fetchs host's OS version through SSH
    :return: str with version
    """
    cmd = ssh.command('cat /etc/redhat-release')
    if cmd.stdout:
        version_description = cmd.stdout[0]
        version_re = (
            r'Red Hat Enterprise Linux Server release (?P<version>\d(\.\d)*)'
        )
        result = re.search(version_re, version_description)
        if result:
            host_os_version = 'RHEL{}'.format(result.group('version'))
            LOGGER.debug('Host version: {}'.format(host_os_version))
            return host_os_version

    LOGGER.warning('Host version not available: {!r}'.format(cmd))
    return 'Not Available'


_SAT_6_2_VERSION_COMMAND = (
    u'grep "SATELLITE_SHORT_VERSION" '
    u'/opt/theforeman/tfm/root/usr/share/gems/gems/foreman_theme_satellite-0'
    u'.1.25/lib/foreman_theme_satellite/version.rb'
)

_SAT_6_1_VERSION_COMMAND = (
    u'grep "VERSION" /usr/share/foreman/lib/satellite/version.rb'
)


@lru_cache(maxsize=1)
def get_host_sat_version():
    """Fetchs host's Satellite version through SSH
    :return: Satellite version
    :rtype: version
    """
    commands = (
        _extract_sat_version(c) for c in
        (_SAT_6_2_VERSION_COMMAND, _SAT_6_1_VERSION_COMMAND)
    )
    for version, ssh_result in commands:
        if version != 'Not Available':
            LOGGER.debug('Host Satellite version: {}'.format(version))
            return version

    LOGGER.warning(
        'Host Satellite version not available: {!r}'.format(ssh_result)
    )
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
        version_re = (
            r'[^\d]*(?P<version>\d(\.\d){1})'
        )
        result = re.search(version_re, version_description)
        if result:
            host_sat_version = result.group('version')
            return host_sat_version, ssh_result

    return 'Not Available', ssh_result


if __name__ == '__main__':
    from robottelo.config import settings
    settings.configure()
    print(get_host_sat_version())


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
