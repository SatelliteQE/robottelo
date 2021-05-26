"""Implements decorator regarding satellite host"""
from functools import wraps

import unittest2

from robottelo.config import settings
from robottelo.host_info import get_host_os_version
from robottelo.logging import logger


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

    :param  tuple versions: args containing host versions for which test
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

            def log_version_info(msg, template):
                logger.debug(template, func.__name__, func.__module__, msg)

            if not settings.configured:
                settings.configure()

            host_version = get_host_os_version()

            if any(host_version.startswith(version) for version in versions):
                skip_msg = f'host {host_version} in ignored versions {versions}'
                skip_template = 'Skipping test %s in module %s due to %s'
                log_version_info(skip_msg, skip_template)
                raise unittest2.SkipTest(skip_msg)

            return func(*args, **kwargs)

        return wrapper

    return decorator
