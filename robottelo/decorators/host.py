import logging
import re
import six
import unittest2

from robottelo import ssh
from robottelo.config import settings
from functools import wraps

if six.PY3:
    from functools import lru_cache
elif six.PY2:
    # workaround only for this module, its not doing exactly the same as
    # original from Python 3, but it fits this specific case
    def lru_cache(maxsize):
        def decorator(func):
            cache = []

            @wraps(func)
            def wrapper():
                if not cache:
                    cache.append(func())
                return cache[0]

            return wrapper

        return decorator

LOGGER = logging.getLogger(__name__)


def _get_host_os_version():
    """Fetchs host's OS version through SSH
    :return: str with version
    """
    cmd = ssh.command('cat /etc/redhat-release')
    if cmd.stdout:
        version_description = cmd.stdout[0]
        r = r'Red Hat Enterprise Linux Server release (?P<version>\d(\.\d)*).*'
        m = re.search(r, version_description)
        if m:
            return 'RHEL{}'.format(m.group('version'))

    LOGGER.warning('Host version not available: {!r}'.format(cmd))
    return 'Not Available'


# not decorating _get_host_os_version to make test easier
@lru_cache(maxsize=1)
def _cached_host_os_version():
    return _get_host_os_version()


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
        """Wrap test methods in order to skip them accordingly with host version.
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapper that will skip the test if one of defined versions
            match host's version.
            """

            if not settings.configured:
                settings.configure()

            host_version = _cached_host_os_version()

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


if __name__ == '__main__':
    if not settings.configured:
        settings.configure()
    print(_get_host_os_version())
