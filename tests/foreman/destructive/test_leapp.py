"""Tests for leapp upgrade

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: LEAPP

:Assignee: shwsingh

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from broker import Broker

from robottelo.config import settings


@pytest.mark.skipif(
    str(settings.server.version.release).split('.')[1] != 11
    and settings.server.version.rhel_version > 7,
    reason='Run only on sat6.11el7',
)
def test_positive_leapp(target_sat):
    """Upgrade satellite's RHEL version using leapp

    :id: 761d4503-0b8c-494d-add5-b870fe1b90b9

    :steps:
        1. Get satellite on rhel7
        2. Run job template that upgrades satellite to rhel8
        3. Check results

    :expectedresult:
        1. Rhel version of the satellite has been updated

    :parametrized: no
    """

    Broker().execute(
        job_template="satellite-leapp-upgrade", target_vm=target_sat.name, AnsibleTower="testing"
    )

    result = target_sat.execute('cat /etc/redhat-release')
    assert result.stdout.split()[6][0] == '8'
