"""Tests for IoP Compliance service

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Compliance

:Team: Compliance

:CaseImportance: High

"""

from pathlib import Path
import time
from types import SimpleNamespace

from fauxfactory import gen_string
from wait_for import wait_for

import pytest

from robottelo.logging import logger


@pytest.fixture
def compliance_session(module_target_sat):
    """Provide a UI session for compliance testing."""
    with module_target_sat.ui_session() as session:
        yield session


@pytest.fixture
def compliance_policy(module_target_sat):
    """Provide a compliance policy for testing."""
    policy_title = f"automation_policy_id-{gen_string('alpha')}"
    description = "I am a policy used purely for automation testing. If I am very fresh, then deleting me can cause a test to fail. If I am a little older, feel free to delete me."
    profiles = module_target_sat.api.CloudCompliancePolicy.get_available_profiles(
        module_target_sat.api.CloudCompliancePolicy()._server_config
    )
    assert len(profiles) > 0, "Expected at least one security profile to exist"
    profile_id = profiles[0]['id']
    policy = module_target_sat.api.CloudCompliancePolicy(
        title=policy_title,
        description=description,
        compliance_threshold=80.0,
        profile_id=profile_id,
    ).create()

    yield policy

    policy.delete()


# TODO: report creation is currently stubbed, until we are able to deploy and test
#       compliance properly on satellite
@pytest.fixture
def compliance_report():
    """Provide a compliance report for testing."""
    return SimpleNamespace(title='CIS Workstation L1')


# TODO: This code should provide a basis for creating compliance report entities once we are able
#       to test in satellite
@pytest.fixture
def _compliance_report(module_target_sat, module_org, module_location):
    """Provide a compliance report for testing."""
    # Step 1: Create Satellite Host entity
    host = module_target_sat.api.Host(
        organization=module_org,
        location=module_location,
    ).create()
    hostname = f"Compliance_test_host-{gen_string('alpha')}"
    facts = {
        'operatingsystem': 'RedHat',
        'operatingsystemrelease': '9.4',
    }
    host = module_target_sat.api.Host().upload_facts()

    result = module_target_sat.execute("whoami", timeout='5m')
    logger.info(f'Created host: {host.name} (id={host.id})')

    # Step 2: run insights-client --compliance on the host
    host.run("insights-client --compliance")

    # Step 3: wait until the report is generated
    TIMEOUT = 10
    DELAY = 5
    found = False
    for i in range(TIMEOUT):
        reports = module_target_sat.api.CloudComplianceReport().search()
        for r in reports:
            if host.title in report.host_titles:
                report = r
                found = True
                break
        if found:
            break
        time.sleep(DELAY)
    else:
        raise Exception(f"report not created in {TIMEOUT*DELAY} seconds")

    report_entity = module_target_sat.api.CloudCompliancePolicy(
        title=report.title,
        description=report.description,
        compliance_threshold=80.0,
        profile_id=report.profile_id,
    ).create()

    yield report_entity

    report_entity.delete()



@pytest.mark.e2e
def test_iop_compliance_navigation(compliance_session, compliance_policy, compliance_report):
    """Navigate to every compliance destination and verify each loads.

    :id: af99ae52-49c5-4e70-b7fe-07dd02b1edc7

    :steps:
        1. Navigate to Compliance Reports listing
        2. Navigate to a Report details page
        3. Navigate to SCAP Policies listing
        4. Navigate to a Policy details page
        5. Navigate to the Create Policy wizard

    :expectedresults:
        Every destination loads and its view is displayed.
    """
    # 1. Navigate to Compliance Reports listing
    reports = compliance_session.cloudcompliancereports.read()
    assert len(reports) > 0

    # 2. Navigate to a Report details page
    report_details = compliance_session.cloudcompliancereports.get_report_details(
        compliance_report.title
    )
    assert report_details.is_displayed
    assert 'Report:' in report_details.title.text

    # 3. Navigate to SCAP Policies listing
    policies = compliance_session.cloudcompliancepolicies.read()
    assert len(policies) > 0

    # 4. Navigate to a Policy details page
    policy_details = compliance_session.cloudcompliancepolicies.get_policy_details(
        compliance_policy.title
    )
    assert policy_details.is_displayed
    assert policy_details.details.is_displayed

    # 5. Navigate to the Create Policy wizard
    wizard = compliance_session.cloudcompliancepolicies.create_policy()
    assert wizard.is_displayed
    wizard.cancel_button.click()


@pytest.mark.e2e
def test_iop_compliance_view_and_filter_reports(compliance_session, compliance_report_with_system):
    """View reports list, filter by policy name, verify filtering works.

    :id: dbf66485-d4e1-493f-a40b-09ab6cc4c324

    :steps:
        1. Navigate to the Insights Compliance Reports page
        2. Read all reports
        3. Filter reports by an existing policy name
        4. Verify filtered results contain only matching policies
        5. Filter by a nonexistent policy name
        6. Verify the empty state is displayed

    :expectedresults:
        Filtering narrows the reports table to matching entries only.
    """
    report = compliance_report_with_system.report

    # 1. Navigate to the Insights Compliance Reports page
    # 2. Read all reports
    all_reports = compliance_session.cloudcompliancereports.read()
    assert len(all_reports) > 0, 'No compliance reports found'

    # 3. Filter reports by an existing policy name
    filtered = compliance_session.cloudcompliancereports.search(report.title)

    # 4. Verify filtered results contain only matching policies
    assert len(filtered) > 0, f'No reports found when filtering for "{report.title}"'
    for filtered_report in filtered:
        assert report.title in filtered_report['Policy'], (
            f'Report "{filtered_report["Policy"]}" does not match filter "{report.title}"'
        )

    # 5. Filter by a nonexistent policy name
    empty = compliance_session.cloudcompliancereports.search('nonexistent_policy_xyz_12345')

    # 6. Verify the empty state is displayed
    assert "No matching reports found" in empty[0]['Policy']
