"""Tests for IoP Compliance service

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Compliance

:Team: Compliance

:CaseImportance: High

"""

import random
from types import SimpleNamespace

from fauxfactory import gen_string
from nailgun import client
from nailgun.config import ServerConfig
import pytest

from robottelo.config import settings

GENERIC_POLICY_DESCRIPTION = "I am a policy used purely for automation testing. If I am very fresh, then deleting me can cause a test to fail. If I am a little older, feel free to delete me."


@pytest.fixture
def compliance_session(module_target_sat):
    """Provide a UI session for compliance testing."""
    with module_target_sat.ui_session() as session:
        yield session


@pytest.fixture
def compliance_policy(module_target_sat):
    """Provide a compliance policy for testing."""
    # Get session auth
    session_kwargs = client.get_session_kwargs(
        module_target_sat.url, settings.server.admin_username, settings.server.admin_password
    )

    # Create ServerConfig with session auth
    sat_config = ServerConfig(
        url=module_target_sat.url, auth=None, verify=False, session_kwargs=session_kwargs
    )

    guide = random.choice(
        module_target_sat.api.CloudComplianceSecurityGuide(server_config=sat_config).search()
    )
    profile = random.choice(
        module_target_sat.api.CloudComplianceProfile(
            server_config=sat_config, security_guide=guide
        ).search()
    )
    policy = module_target_sat.api.CloudCompliancePolicy(
        server_config=sat_config,
        title=f"Automation policy {gen_string('alpha')}",
        description=GENERIC_POLICY_DESCRIPTION,
        compliance_threshold=80.0,
        profile_id=profile.id,
    ).create()

    yield policy

    policy.delete()


# TODO: report creation is currently stubbed, until we are able to deploy and test
#       compliance properly on satellite
@pytest.fixture
def compliance_report():
    """Provide a compliance report for testing."""
    return SimpleNamespace(title='ANSSI high (lab)')


@pytest.mark.e2e
def test_iop_compliance_navigation(compliance_session, compliance_policy, compliance_report):
    """Navigate to every compliance destination and verify each loads.

    :id: 962502d2-78db-4bb1-b557-b162d0ad8361

    :steps:
        1. Navigate to Compliance Reports
        2. Navigate to a Report details page
        3. Navigate to SCAP Policies listing
        4. Navigate to a Policy details page
        5. Navigate to the Create Policy wizard

    :expectedresults:
        Every destination loads and its view is displayed.
    """

    # 1. Navigate to Compliance Reports
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


def test_iop_compliance_policy_scan_report_e2e():
    """Test the full E2E workflow for compliance."""
    pass


def test_iop_compliance_policy_update_affects_scan():
    """Test that changing a threshold value affects future scans."""
    pass


# TODO: generate id
def test_iop_compliance_crud_policy(compliance_session):
    """Test that creating a policy via UI works.

    :id: d532c0aa-2ed5-4953-9ff7-99521569c453

    :steps:
        1. Create a customized policy via the Create SCAP policy wizard
        2. Navigate to details of the new policy
        3. Verify policy is displayed correctly
        4. change policy description
        5. change compliance threshold
        6. verify the values have changed
        7. Navigate to all policies
        8. delete the policy using row kebab
        9. verify the policy is deleted

    :expectedresults:
        The created policy exists.
    """
    random_id = gen_string('alpha')
    random_updated_id = gen_string('alpha')

    # 1. Create a customized policy via the Create SCAP policy wizard
    wizard = compliance_session.cloudcompliancepolicies.create_policy()
    wizard.create_scap_policy.select_os(os_name='RHEL 10')
    wizard.create_scap_policy.select_policy_type(policy_name='ANSSI-BP-028 (high)')
    wizard.next()
    random_id = gen_string('alpha')
    wizard.details.change_policy_name(f" - Automation policy {random_id}")
    policy_title = wizard.details.policy_name.read()
    new_description = f"{GENERIC_POLICY_DESCRIPTION} My random code is {random_id}"
    wizard.details.change_description(new_description)
    wizard.details.change_threshold(50)
    wizard.next()
    wizard.next()
    wizard.next()
    wizard.finish()
    wizard.return_to_application()

    # 2. Navigate to details of the new policy
    policy_details = compliance_session.cloudcompliancepolicies.get_policy_details(policy_title)

    # 3. Verify policy is displayed correctly
    assert policy_details.details.threshold_value == '50.0%'
    assert random_id in policy_details.details.policy_description.read()

    # 4. change policy description
    policy_details.details.change_description(
        new_description=f"{GENERIC_POLICY_DESCRIPTION} My random code is {random_updated_id}"
    )

    # 5. change compliance threshold
    policy_details.details.change_threshold(new_threshold=20)

    # 6. verify the values have changed
    compliance_session.cloudcompliancepolicies.read()
    policy_details = compliance_session.cloudcompliancepolicies.get_policy_details(policy_title)
    assert '20' in policy_details.details.threshold_value
    assert random_updated_id in policy_details.details.policy_description.read()

    # 7. Navigate to all policies
    compliance_session.cloudcompliancepolicies.read()

    # 8. delete the policy using row kebab
    compliance_session.cloudcompliancepolicies.delete_policy(policy_name=policy_title)

    # 9. verify the policy is deleted
    policies = compliance_session.cloudcompliancepolicies.read()
    assert len([p for p in policies if random_id in p['Name']]) == 0


def test_iop_compliance_assign_remove_host():
    """Test that it's possible to assign and remove hosts to/from policies."""
    pass


def test_iop_compliance_assign_host_group_to_policy():
    """Test that it's possible to assign a host group to policy."""
    pass


@pytest.mark.e2e
def test_iop_compliance_view_and_filter_reports(compliance_session, compliance_report):
    """View reports list, filter by policy name, verify filtering works.

    :id: 07b167c4-d81c-4817-8b9d-d5a58400d5e9

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
    # report = compliance_report_with_system.report

    # 1. Navigate to the Insights Compliance Reports page
    # 2. Read all reports
    all_reports = compliance_session.cloudcompliancereports.read()
    assert len(all_reports) > 0, 'No compliance reports found'

    # 3. Filter reports by an existing policy name
    filtered = compliance_session.cloudcompliancereports.search(compliance_report.title)

    # 4. Verify filtered results contain only matching policies
    assert len(filtered) > 0, f'No reports found when filtering for "{compliance_report.title}"'
    for filtered_report in filtered:
        assert compliance_report.title in filtered_report['Policy'], (
            f'Report "{filtered_report["Policy"]}" does not match filter "{compliance_report.title}"'
        )

    # 5. Filter by a nonexistent policy name
    empty = compliance_session.cloudcompliancereports.search('nonexistent_policy_xyz_12345')

    # 6. Verify the empty state is displayed
    assert "No matching reports found" in empty[0]['Policy']


def test_iop_compliance_view_report_details():
    """Test that we can see Compliance report details correctly."""
    pass


def test_iop_compliance_rbac_view_only():
    """Test that a user with a read-only role can only view policies and reports."""
    pass


def test_iop_compliance_rbac_edit():
    """Test that a user with ForemanRHCloud role can CRUD policies and reports."""
    pass


def test_iop_compliance_rbac_no_access():
    """Test that a user without any permissions can not access any Compliance content."""
    pass
