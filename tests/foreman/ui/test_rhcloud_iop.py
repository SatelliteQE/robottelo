"""Tests for RH Cloud - IOP

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:Team: Proton

:CaseImportance: High

"""

from datetime import UTC, datetime, timedelta
import os
import tempfile

import pytest
from wait_for import wait_for

from robottelo.constants import DEFAULT_LOC, OPENSSH_RECOMMENDATION
from robottelo.enums import NetworkType
from robottelo.utils.io import get_report_data
from tests.foreman.ui.test_rhcloud_insights import (
    create_insights_vulnerability as create_insights_recommendation,
)
from tests.foreman.ui.test_rhcloud_inventory import common_assertion


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

        # Verify that the Satellite is not affected by SAT-35946
        result = module_target_sat_insights.execute(
            'grep "502 Bad Gateway" /var/log/foreman/production.log'
        )
        assert result.status != 0

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


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('10')
@pytest.mark.parametrize('module_target_sat_insights', [False], ids=['local'], indirect=True)
@pytest.mark.usefixtures('setting_update')
@pytest.mark.parametrize(
    'setting_update',
    ['subscription_connection_enabled=false'],
    indirect=True,
)
def test_iop_rhcloud_inventory_e2e(
    module_target_sat_insights,
    rhcloud_manifest_org,
    rhel_insights_vm,
):
    """Generate inventory report and verify its basic properties. Since this is an on-prem scenario,
    set subscription_connection_enabled to false.

    :id: 7041b3d2-c639-4ae1-97db-94a735bf8c49

    :parametrized: yes

    :customerscenario: true

    :expectedresults:

        1. Report can be generated.
        2. Report can be downloaded.
        3. Report has non-zero size.
        4. Report can be extracted.
        5. JSON files inside report can be parsed.
        6. metadata.json lists all and only slice JSON files in tar.
        7. Host counts in metadata matches host counts in slices.
        8. Assert hostname, IP address, and installed packages are present in the report.

    :CaseImportance: Critical

    :BZ: 1807829

    :Verifies: SAT-44052
    """
    org = rhcloud_manifest_org
    host = rhel_insights_vm
    satellite = module_target_sat_insights

    with satellite.ui_session() as session:
        session.organization.select(org_name=org.name)
        session.location.select(loc_name=DEFAULT_LOC)
        timestamp = (datetime.now(UTC) - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.iopcloudinventory.generate_report_only(org.name)
        wait_for(
            lambda: (
                satellite.api.ForemanTask()
                .search(
                    query={
                        'search': f'label = ForemanInventoryUpload::Async::HostInventoryReportJob '
                        f'and started_at >= "{timestamp}"'
                    }
                )[0]
                .result
                == 'success'
            ),
            timeout=400,
            delay=15,
            silent_failure=True,
            handle_exception=True,
        )
        remote_report_path = (
            f'/var/lib/foreman/red_hat_inventory/generated_reports/report_for_{org.id}.tar.xz'
        )

        # Verify file exists on Satellite
        result = satellite.execute(f'test -f {remote_report_path}')
        assert result.status == 0, f"Report file not found at {remote_report_path}"

        # Copy report from Satellite to local temp location
        temp_dir = tempfile.mkdtemp()
        local_report_name = f'report_for_{org.id}.tar.xz'
        report_path = os.path.join(temp_dir, local_report_name)

        # Download the file from satellite
        satellite.get(remote_path=remote_report_path, local_path=report_path)
        inventory_data = session.iopcloudinventory.read(org.name)

    # Verify that the generated archive is valid
    common_assertion(
        report_path, inventory_data, org, satellite, subscription_connection_enabled=False
    )

    # Get report data for assertion
    host_json_data = get_report_data(report_path)['hosts'][0]

    # Verify that hostname in report matches hostname of host object
    assert host.hostname == host_json_data['fqdn']

    # Verify that ip_addresses are present report
    is_ipv6 = satellite.network_type == NetworkType.IPV6
    key = 'ipv6_addresses' if is_ipv6 else 'ipv4_addresses'
    ip_address = host_json_data['system_profile']['network_interfaces'][0][key]
    assert host.ip_addr in ip_address

    # Verify that packages are included in report
    assert 'installed_packages' in host_json_data['system_profile']
    assert len(host_json_data['system_profile']['installed_packages']) > 1


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


@pytest.mark.parametrize("module_target_sat_insights", [False], ids=["local"], indirect=True)
def test_iop_negative_rhcloud_inventory_upload_not_displayed(module_target_sat_insights):
    """Verify that the 'Red Hat Lightspeed > Inventory Upload' navigation item is not available
    when the Satellite is configured to use IoP.

    :id: 84023ae9-7bc4-4332-9aaf-749d6c48c2d2

    :steps:
        1. Configure Satellite with IOP
        2. Check that 'Inventory Upload' is not visible under 'Red Hat Lightspeed'.

    :expectedresults:
        1. "Inventory Upload" is not visible under "Red Hat Lightspeed".
    """
    with module_target_sat_insights.ui_session() as session:
        view = session.dashboard.navigate_to(session.dashboard, 'All')
        with pytest.raises(Exception, match='not found in navigation tree'):
            view.menu.select('Red Hat Lightspeed', 'Inventory Upload')


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
