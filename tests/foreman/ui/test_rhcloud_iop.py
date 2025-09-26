"""Tests for RH Cloud - IOP

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: RHCloud

:Team: Proton

:CaseImportance: High

"""

import pytest

from robottelo.constants import OPENSSH_RECOMMENDATION


def create_insights_vulnerability(host):
    """Function to create vulnerabilities that can be remediated."""

    # Add vulnerability for DNF_RECOMMENDATION (RHEL 8+)
    if host.os_version.major > 7:
        host.run('dnf update -y dnf;sed -i -e "/^best/d" /etc/dnf/dnf.conf')

    # Add vulnerability for SSH_RECOMMENDATION
    host.run('chmod 777 /etc/ssh/sshd_config')

    # Upload insights data to Satellite
    result = host.run('insights-client')
    assert result.status == 0


@pytest.mark.e2e
@pytest.mark.pit_server
@pytest.mark.pit_client
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('N-1')
def test_iop_recommendations_e2e(
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_satellite_iop,
):
    """Set up Satellite with iop enabled, create vulnerability, and apply remediation.

    :id: 84bb1530-acdc-418c-8577-57fcfec138c6

    :steps:
        1. Set up Satellite with iop enabled.
        2. In Satellite UI, go to Red Hat Lightspeed > Recommendations.
        3. Run remediation for "OpenSSH config permissions" recommendation against host.
        4. Verify that the remediation job completed successfully.
        5. Search for previously remediated issue.

    :expectedresults:
        1. Red Hat Lightspeed recommendation related to "OpenSSH config permissions" issue is listed
            for misconfigured machine.
        2. Remediation job finished successfully.
        3. Red Hat Lightspeed recommendation related to "OpenSSH config permissions" issue is not listed.

    :CaseImportance: Critical

    :Verifies: SAT-32566

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org_name = rhcloud_manifest_org.name

    # Verify insights-client can update to latest version available from server
    assert rhel_insights_vm.execute('insights-client --version').status == 0

    # Prepare misconfigured machine and upload data to Insights
    create_insights_vulnerability(rhel_insights_vm)

    with module_satellite_iop.ui_session() as session:
        session.organization.select(org_name=org_name)

        # Verify that we can see the rule hit via insights-client
        result = rhel_insights_vm.execute('insights-client --diagnosis')
        assert result.status == 0
        assert 'OPENSSH_HARDENING_CONFIG_PERMS' in result.stdout

        # Search for the recommendation.
        result = session.recommendationstab.search(OPENSSH_RECOMMENDATION)
        assert result[0]['Name'] == OPENSSH_RECOMMENDATION

        # Remediate the Affected System.
        result = session.recommendationstab.remediate_affected_system(
            OPENSSH_RECOMMENDATION, rhel_insights_vm.hostname
        )

        # Verify that the job Succeeded
        assert result['status']['Succeeded'] != 0
        assert result['overall_status']['is_success']

        # Verify that the recommendation is not listed anymore.
        assert (
            'No recommendations None of your connected systems are affected by enabled recommendations'
            in session.recommendationstab.search(OPENSSH_RECOMMENDATION)[0]['Name']
        )


@pytest.mark.e2e
@pytest.mark.pit_server
@pytest.mark.pit_client
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('N-1')
def test_iop_recommendations_remediate_multiple_hosts(
    rhel_insights_vms,
    rhcloud_manifest_org,
    module_satellite_iop,
):
    """Set up Satellite with iop enabled, register multiple hosts, create vulnerabilities on both hosts,
        and bulk apply remediation.

    :id: 5b29a791-b42a-4ab9-b632-cab919d06daa

    :steps:
        1. Set up Satellite with iop enabled and register multiple hosts.
        2. In Satellite UI, go to Red Hat Lightspeed > Recommendations.
        3. Run remediation for "OpenSSH config permissions" recommendation against multiple hosts.
        4. Verify that the remediation job completed successfully.
        5. Search for previously remediated issue.

    :expectedresults:
        1. Red Hat Lightspeed recommendation related to "OpenSSH config permissions" issue is listed
            for misconfigured machines.
        2. Remediation job finished successfully.
        3. Red Hat Lightspeed recommendation related to "OpenSSH config permissions" issue is not listed.

    :CaseImportance: Critical

    :Verifies: SAT-32566

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org_name = rhcloud_manifest_org.name
    hostnames = [host.hostname for host in rhel_insights_vms]

    # Prepare misconfigured machines and upload data to Insights
    for vm in rhel_insights_vms:
        create_insights_vulnerability(vm)

    with module_satellite_iop.ui_session() as session:
        session.organization.select(org_name=org_name)

        # Search for the recommendations
        result = session.recommendationstab.search(OPENSSH_RECOMMENDATION)

        assert result[0]['Name'] == OPENSSH_RECOMMENDATION
        assert result[0]['Systems'] == '2'

        # Bulk remediate the Affected System.
        result = session.recommendationstab.bulk_remediate_affected_systems(OPENSSH_RECOMMENDATION)

        # Verify that the job Succeeded
        assert result['status']['Succeeded'] != 0
        assert result['overall_status']['is_success']
        assert len(result['hosts']) == len(rhel_insights_vms)
        assert all(result['hosts'] in hostnames for result in result)

        # Verify that the expected hostnames are in results
        expected = {h.strip().lower() for h in hostnames}
        found = {r['Name'].strip().lower() for r in result['hosts']}
        missing = expected - found
        assert not missing, f"Missing hosts in results: {sorted(missing)}"
        # Verify that the recommendation is not listed anymore.
        assert (
            'No recommendations None of your connected systems are affected by enabled recommendations'
            in session.recommendationstab.search(OPENSSH_RECOMMENDATION)[0]['Name']
        )
