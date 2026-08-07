"""Tests for IoP Compliance service

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Compliance

:Team: Compliance

:CaseImportance: High

"""

from types import SimpleNamespace

from airgun.session import Session
import pytest

# The colleague's Foreman instance with the compliance plugin
FOREMAN_HOST = 'ip-10-0-168-248.rhos-01.prod.psi.rdu2.redhat.com'


@pytest.fixture
def compliance_session():
    """Provide a UI session for compliance testing.

    TODO: Replace with target_sat.ui_session() once integrated with Broker.
    """
    with Session(
        session_name='compliance_test',
        hostname=FOREMAN_HOST,
        user='admin',
        password='changeme',
    ) as session:
        yield session


@pytest.fixture
def compliance_policy():
    """Provide a compliance policy for testing.

    TODO: Create the policy via the wizard/API and clean it up after the test.
    Currently returns a stub with .name matching an existing policy on the instance.
    """
    return SimpleNamespace(name='CIS Workstation L1')


@pytest.fixture
def compliance_report():
    """Provide a compliance report for testing.

    TODO: Create a policy, trigger a scan, wait for a report to appear.
    Currently returns a stub with .policy_name matching an existing report on the instance.
    """
    return SimpleNamespace(policy_name='CIS Workstation L1')


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
        compliance_report.policy_name
    )
    assert report_details.is_displayed
    assert 'Report:' in report_details.title.text

    # 3. Navigate to SCAP Policies listing
    policies = compliance_session.cloudcompliancepolicies.read()
    assert len(policies) > 0

    # 4. Navigate to a Policy details page
    policy_details = compliance_session.cloudcompliancepolicies.get_policy_details(
        compliance_policy.name
    )
    assert policy_details.is_displayed
    assert policy_details.details.is_displayed

    # 5. Navigate to the Create Policy wizard
    wizard = compliance_session.cloudcompliancepolicies.create_policy()
    assert wizard.is_displayed
    wizard.cancel_button.click()


@pytest.mark.e2e
def test_iop_compliance_view_and_filter_reports(compliance_session, compliance_report):
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
    # 1. Navigate to the Insights Compliance Reports page
    # 2. Read all reports
    all_reports = compliance_session.cloudcompliancereports.read()
    assert len(all_reports) > 0, 'No compliance reports found'

    # 3. Filter reports by an existing policy name
    filtered = compliance_session.cloudcompliancereports.search(compliance_report.policy_name)

    # 4. Verify filtered results contain only matching policies
    assert len(filtered) > 0, (
        f'No reports found when filtering for "{compliance_report.policy_name}"'
    )
    for report in filtered:
        assert compliance_report.policy_name in report['Policy'], (
            f'Report "{report["Policy"]}" does not match filter "{compliance_report.policy_name}"'
        )

    # 5. Filter by a nonexistent policy name
    empty = compliance_session.cloudcompliancereports.search('nonexistent_policy_xyz_12345')

    # 6. Verify the empty state is displayed
    assert len(empty) == 1
    assert 'No matching reports found' in empty[0]['Policy']
    view = compliance_session.cloudcompliancereports.navigate_to(
        compliance_session.cloudcompliancereports, 'All'
    )
    assert view.empty_state.is_displayed
