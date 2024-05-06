"""Tests for leapp upgrade of Satellite

:CaseAutomation: Automated

:CaseComponent: Upgrades

:Team: Platform

:CaseImportance: High

"""

from broker import Broker
import pytest

from robottelo.hosts import get_sat_rhel_version, get_sat_version


@pytest.mark.e2e
@pytest.mark.skipif(
    get_sat_version().minor != 11 and get_sat_rhel_version().major > 7,
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
    """
    # Getting original RHEL version so we can increment it later in the test
    orig_rhel_ver = target_sat.os_version.major
    Broker().execute(
        job_template="satellite-leapp-upgrade",
        target_vm=target_sat.name,
    )
    # Recreate the session object within a Satellite object after upgrading
    target_sat.connect()
    # Clean cached properties after the upgrade
    target_sat.clean_cached_properties()
    # Get RHEL version after upgrading
    res_rhel_version = target_sat.os_version.major
    # Check if RHEL was upgraded
    assert res_rhel_version == orig_rhel_ver + 1, 'RHEL was not upgraded'
    # Check satellite's health
    sat_health = target_sat.execute('satellite-maintain health check')
    assert sat_health.status == 0, 'Satellite health check failed'
