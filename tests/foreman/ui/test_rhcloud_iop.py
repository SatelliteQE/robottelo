"""Tests for RH Cloud - IOP

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:Team: Proton

:CaseImportance: High

"""

import pytest

from robottelo.constants import OPENSSH_RECOMMENDATION
from tests.foreman.ui.test_rhcloud_insights import (
    create_insights_vulnerability as create_insights_recommendation,
)


@pytest.mark.e2e
@pytest.mark.pit_server
@pytest.mark.pit_client
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(r'^(?![78]).*')
@pytest.mark.parametrize('module_target_sat_insights', [False], ids=['local'], indirect=True)
def test_iop_recommendations_e2e(
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat_insights,
):
    """Set up Satellite with iop enabled, create conditions to cause advisor recommendation,
    and apply remediation.

    :id: 84bb1530-acdc-418c-8577-57fcfec138c6

    :steps:
        1. Set up Satellite with iop enabled.
        2. In Satellite UI, go to Red Hat Lightspeed > Recommendations.
        3. Run remediation for "OpenSSH config permissions" recommendation against host.
        4. Verify that the remediation job completed successfully.
        5. Search for previously remediated issue.
        6. Unregister host from insights

    :expectedresults:
        1. Red Hat Lightspeed recommendation related to "OpenSSH config permissions" issue is listed
            for misconfigured machine.
        2. Remediation job finished successfully.
        3. Red Hat Lightspeed recommendation related to "OpenSSH config permissions" issue is not listed.
        4. Host was successfully unregistered from insights

    :CaseImportance: Critical

    :Verifies: SAT-32566

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org_name = rhcloud_manifest_org.name

    # Verify insights-client package is installed
    assert rhel_insights_vm.execute('insights-client --version').status == 0

    # Prepare misconfigured machine and upload data to Insights
    create_insights_recommendation(rhel_insights_vm)

    with module_target_sat_insights.ui_session() as session:
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

        # Verify that unregistering host succeeded
        result = rhel_insights_vm.execute('insights-client --unregister')
        assert 'Successfully unregistered from the Red Hat Insights Service' in result.stdout
        result = rhel_insights_vm.execute('insights-client --status')
        assert 'System is NOT registered locally' in result.stdout


@pytest.mark.e2e
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(r'^(?![78]).*')
@pytest.mark.parametrize('module_target_sat_insights', [False], ids=['local'], indirect=True)
def test_iop_recommendations_remediate_multiple_hosts(
    rhel_insights_vms,
    rhcloud_manifest_org,
    module_target_sat_insights,
):
    """Set up Satellite with iop enabled, register multiple hosts, create conditions that violate
    advisor rules on both hosts, and bulk apply remediation.

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
        create_insights_recommendation(vm)

    with module_target_sat_insights.ui_session() as session:
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


@pytest.mark.e2e
@pytest.mark.pit_server
@pytest.mark.pit_client
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(r'^(?![78]).*')
@pytest.mark.parametrize('module_target_sat_insights', [False], ids=['local'], indirect=True)
def test_iop_recommendations_host_details_e2e(
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat_insights,
):
    """Set up Satellite with iop enabled, create condition on the host that violates advisor rules,
    see the recommendation on the host details page, and apply the remediation.

    :id: 282a7ef0-33a4-4dd4-8712-064a30cb54c6

    :steps:
        1. Set up Satellite with iop enabled.
        2. In Satellite UI, go to All Hosts > Hostname > Recommendations.
        3. Run remediation for "OpenSSH config permissions" recommendation against host.
        4. Verify that the remediation job completed successfully.
        5. Search for previously remediated issue.

    :expectedresults:
        1. Host recommendation related to "OpenSSH config permissions" issue is listed
            for misconfigured machine.
        2. Remediation job finished successfully.
        3. Host recommendation related to "OpenSSH config permissions" issue is not listed.

    :CaseImportance: Critical

    :Verifies: SAT-32566

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org_name = rhcloud_manifest_org.name

    # Verify insights-client package is installed
    assert rhel_insights_vm.execute('insights-client --version').status == 0

    # Prepare misconfigured machine and upload data to Insights
    create_insights_recommendation(rhel_insights_vm)

    with module_target_sat_insights.ui_session() as session:
        session.organization.select(org_name=org_name)

        # Verify that we can see the rule hit via insights-client
        result = rhel_insights_vm.execute('insights-client --diagnosis')
        assert result.status == 0
        assert 'OPENSSH_HARDENING_CONFIG_PERMS' in result.stdout

        result = session.host_new.get_recommendations(rhel_insights_vm.hostname)

        assert any(row.get('Description') == OPENSSH_RECOMMENDATION for row in result), (
            f"No row found with Recommendation == {OPENSSH_RECOMMENDATION}"
        )
        # Remediate the Affected System.
        result = session.host_new.remediate_host_recommendation(
            rhel_insights_vm.hostname,
            OPENSSH_RECOMMENDATION,
        )
        # Verify that the job Succeeded
        assert result['status']['Succeeded'] != 0
        assert result['overall_status']['is_success']

        # Verify that the recommendation is not listed anymore.
        result = session.host_new.get_recommendations(rhel_insights_vm.hostname)
        assert not any(row.get('Description') == OPENSSH_RECOMMENDATION for row in result), (
            f"Recommendation found: {OPENSSH_RECOMMENDATION}"
        )


# @pytest.mark.parametrize("module_target_sat_insights", [False], ids=["local"], indirect=True)
def test_rhcloud_inventory_disabled_local_insights(module_target_sat_insights):
    """Verify that the 'Red Hat Lightspeed > Inventory Upload' navigation item is not available
    when the Satellite is configured to use IoP.

    :id: 84023ae9-7bc4-4332-9aaf-749d6c48c2d2

    :steps:
        1. Configure Satellite to use local Insights advisor engine.
        2. Navigate to the Insights Recommendations page.
        3. Select Insights > Inventory Upload from the navigation menu.

    :expectedresults:
        1. "Inventory Upload" is not visible under "Insights".

    :CaseImportance: Medium

    :CaseAutomation: Automated
    """
    with module_target_sat_insights.ui_session() as session:
        insights_view = session.cloudinsights.navigate_to(session.cloudinsights, 'All')
        with pytest.raises(Exception, match='not found in navigation tree'):
            insights_view.menu.select('Insights', 'Inventory Upload')


@pytest.mark.e2e
@pytest.mark.no_containers
@pytest.mark.rhel_ver_match(r'^(?![78]).*')
@pytest.mark.parametrize('module_target_sat_insights', [False], ids=['local'], indirect=True)
def test_iop_recommendations_remediation_type_and_status(
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat_insights,
):
    """Set up Satellite with iop enabled, verify recommendations remediation type,
    and test filtering recommendations by status.

    :id: 62834698-b4b8-4218-855c-2b2aa584b364

    :steps:
        1. Set up Satellite with iop enabled.
        2. In Satellite UI, go to Red Hat Lightspeed > Recommendations.
        3. Search for "OpenSSH config permissions" recommendation.
        4. Verify the recommendation's remediation type is "Playbook".
        5. Apply filter for "Enabled" status recommendations.
        6. Verify Enabled recommendations are greater than 0.
        7. Apply filter for "Disabled" status recommendations.
        8. Verify Disabled recommendations are 0.

    :expectedresults:
        1. Red Hat Lightspeed recommendation related to "OpenSSH config permissions" issue is listed
            for misconfigured machine.
        2. The recommendation has remediation type "Playbook".
        3. Enabled recommendations are displayed (count greater than 0).
        4. No disabled recommendations are displayed.

    :CaseImportance: Critical

    :Verifies: SAT-32566

    :parametrized: yes

    :CaseAutomation: Automated
    """
    org_name = rhcloud_manifest_org.name

    # Verify insights-client package is installed
    assert rhel_insights_vm.execute('insights-client --version').status == 0

    # Prepare misconfigured machine and upload data to Insights
    create_insights_recommendation(rhel_insights_vm)

    with module_target_sat_insights.ui_session() as session:
        session.organization.select(org_name=org_name)

        # Verify that we can see the rule hit via insights-client
        result = rhel_insights_vm.execute('insights-client --diagnosis')
        assert result.status == 0
        assert 'OPENSSH_HARDENING_CONFIG_PERMS' in result.stdout

        # Search for the recommendation and assert its remediation type
        result = session.recommendationstab.search(OPENSSH_RECOMMENDATION)
        assert result[0]['Name'] == OPENSSH_RECOMMENDATION
        assert result[0]['Remediation type'] == 'Playbook'

        # Verify that enabled recommendations are greater than 0
        result = session.recommendationstab.apply_filter("Status", "Enabled")
        assert len(result) > 0

        # Verify that Disabled recommnedations are 0
        result = session.recommendationstab.apply_filter("Status", "Disabled")
        assert 'No recommendations' in result[0]['Name']
