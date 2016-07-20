"""Implements decorator regarding satellite host"""
import logging
import re
import unittest2

from robottelo import ssh
from robottelo.config import settings
from robottelo.helpers import lru_cache
from functools import wraps

LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_host_os_version():
    """Fetchs host's OS version through SSH
    :return: str with version
    """
    cmd = ssh.command('cat /etc/redhat-release')
    if cmd.stdout:
        version_description = cmd.stdout[0]
        version_re = (
            r'Red Hat Enterprise Linux Server release (?P<version>\d(\.\d)*).*'
        )
        result = re.search(version_re, version_description)
        if result:
            return 'RHEL{}'.format(result.group('version'))

    LOGGER.warning('Host version not available: {!r}'.format(cmd))
    return 'Not Available'


def skip_if_os(*versions):
    """Decorator to skip tests based on host version

    If the calling function uses 'RHEL6' - test will be skipped for RHEL6,
    but will run for whatever another version, e.g, RHEL5, RHEL6.1, RHEL7,
    and so on

    Note: If the version can't be obtained, tests will run

    Usage:

    To skip a specific test::

        from robottelo.decorators.host import skip_if_host_is

        @skip_if_os('RHEL6')
        def test_hostgroup_create():
            # test code continues here

    :param  tuple versions: *args containing host versions for which test
    must be skipped
    :returns: ``unittest2.skipIf``
    """
    versions = set(map(lambda s: s.upper(), versions))

    def decorator(func):
        """Wrap test methods in order to skip them accordingly with host
        version.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper that will skip the test if one of defined versions
            match host's version.
            """

            if not settings.configured:
                settings.configure()

            host_version = _get_host_os_version()

            if host_version in versions:
                skip_msg = 'host {0} in ignored versions {1}'.format(
                    host_version,
                    versions
                )
                LOGGER.debug(
                    'Skipping test %s in module %s due to %s',
                    func.__name__,
                    func.__module__,
                    skip_msg
                )
                raise unittest2.SkipTest(skip_msg)
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator
