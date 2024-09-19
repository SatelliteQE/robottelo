"""Test for bootstrap script (bootstrap.py)

:Requirement: Bootstrap Script

:CaseAutomation: Automated

:CaseComponent: Bootstrap

:Team: Platform

:CaseImportance: High

"""

from time import sleep

import pytest

from robottelo.config import settings
from robottelo.logging import logger


@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_os_version(rhel_contenthost):
    """System has os_version

    :id: e34561fd-e0d6-4587-84eb-f86bd131aab1

    :steps:

        1. Check system os_version

    :expectedresults: Success

    :CaseAutomation: Automated

    :CaseImportance: Critical

    :customerscenario: true

    :BZ: 2001476
    """
    for _ in range(5):
        result = rhel_contenthost.execute('cat /etc/os-release')
        logger.info(f"tpapaioa os-release {result=}")

    sleep(10)
    assert rhel_contenthost.os_version
