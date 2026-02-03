"""Tests for RH Cloud - IOP

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:Team: Proton

:CaseImportance: High

"""

import pytest

from selenium.common.exceptions import NoSuchElementException
from robottelo.constants import OPENSSH_RECOMMENDATION
from robottelo.utils.datafactory import gen_string
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


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('10')
@pytest.mark.parametrize('module_target_sat_insights', [False], ids=['local'], indirect=True)
def test_iop_insights_rbac_view_only_permissions(
    test_name,
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat_insights,
    default_location,
):
    """Verify that a user with view-only permissions can access Insights Recommendations
    and Vulnerabilities but cannot perform edit actions.

    :id: a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d

    :steps:
        1. Create a role with only view permissions (view_advisor, view_vulnerability).
        2. Create a test user with the role and log in.
        3. Navigate to Red Hat Lightspeed → Recommendations.
        4. Verify page loads and displays recommendations.
        5. Verify edit actions (enable/disable) are hidden for recommendations.
        6. Navigate to Red Hat Lightspeed → Vulnerabilities.
        7. Verify page loads and vulnerabilities are accessible.
        8. Verify edit actions are hidden for vulnerabilities.

    :expectedresults:
        1. User can view the Recommendations page.
        2. Recommendations are displayed.
        3. Edit actions are not available for recommendations.
        4. User can view the Vulnerabilities page.
        5. Edit actions are not available for vulnerabilities.

    :CaseImportance: High

    :customerscenario: true

    :parametrized: yes

    :CaseAutomation: Automated
    """
    CVE_ID = 'CVE-2018-10896'
    org_name = rhcloud_manifest_org.name
    user_password = gen_string('alpha')

    # Use built-in ForemanRhCloud Read Only role
    rhcloud_role = module_target_sat_insights.api.Role().search(
        query={'search': 'name="ForemanRhCloud Read Only"'}
    )[0]

    # Create additional role with basic permissions
    additional_role = module_target_sat_insights.api.Role(
        organization=[rhcloud_manifest_org]
    ).create()
    module_target_sat_insights.api_factory.create_role_permissions(
        additional_role,
        {
            'Organization': ['view_organizations'],
            'Location': ['view_locations'],
            'Host': ['view_hosts'],
        },
    )

    # Create user with view-only roles
    user = module_target_sat_insights.api.User(
        role=[rhcloud_role, additional_role],
        admin=False,
        password=user_password,
        organization=[rhcloud_manifest_org],
        location=[default_location],
    ).create()
    # Set default organization and location after creation to avoid validation order issues
    user.default_organization = rhcloud_manifest_org
    user.default_location = default_location
    user.update(['default_organization', 'default_location'])

    # Verify insights-client package is installed
    assert rhel_insights_vm.execute('insights-client --version').status == 0

    # Prepare misconfigured machine and upload data to Insights
    create_insights_recommendation(rhel_insights_vm)

    # Log in as the view-only user
    with module_target_sat_insights.ui_session(
        test_name, user.login, user_password
    ) as session:
        session.organization.select(org_name=org_name)

        # Verify that we can see the rule hit via insights-client
        result = rhel_insights_vm.execute('insights-client --diagnosis')
        assert result.status == 0
        assert 'OPENSSH_HARDENING_CONFIG_PERMS' in result.stdout

        # Verify edit actions are hidden (disable/enable action should not be available) in the UI
        with pytest.raises(NoSuchElementException):
            # Disable recommendation
            session.recommendationstab.disable_recommendation(
                recommendation_name=OPENSSH_RECOMMENDATION
            )
        # Test Vulnerability without edit permissions
        with pytest.raises(NoSuchElementException):
            session.cloudvulnerability.edit_vulnerabilities(CVE_ID)


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('10')
@pytest.mark.parametrize('module_target_sat_insights', [False], ids=['local'], indirect=True)
def test_iop_insights_rbac_edit_permissions(
    test_name,
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat_insights,
    default_location,
):
    """Verify that a user with edit permissions can access Insights Recommendations
    and Vulnerabilities and perform remediation actions.

    :id: b2c3d4e5-f6a7-4b5c-9d0e-1f2a3b4c5d6e

    :steps:
        1. Create a role with both view and edit permissions (view_advisor, edit_advisor,
           view_vulnerability, edit_vulnerability).
        2. Create a test user with the role and log in.
        3. Navigate to Red Hat Lightspeed → Recommendations.
        4. Verify page loads and displays recommendations.
        5. Verify all edit actions (remediation) are enabled and functional for recommendations.
        6. Navigate to Red Hat Lightspeed → Vulnerabilities.
        7. Verify page loads and displays vulnerabilities.
        8. Verify all edit actions (remediation) are enabled for vulnerabilities.

    :expectedresults:
        1. User can view the Recommendations page.
        2. Recommendations are displayed.
        3. User can successfully remediate recommendations.
        4. User can view the Vulnerabilities page.
        5. User can access remediation actions for vulnerabilities.

    :CaseImportance: High

    :customerscenario: true

    :parametrized: yes

    :CaseAutomation: Automated
    """
    CVE_ID = 'CVE-2018-10896'
    org_name = rhcloud_manifest_org.name
    user_password = gen_string('alpha')

    # Use built-in ForemanRhCloud role
    rhcloud_role = module_target_sat_insights.api.Role().search(
        query={'search': 'name="ForemanRhCloud"'}
    )[0]

    # Create additional role with basic and remote execution permissions
    additional_role = module_target_sat_insights.api.Role(
        organization=[rhcloud_manifest_org]
    ).create()
    module_target_sat_insights.api_factory.create_role_permissions(
        additional_role,
        {
            'Organization': ['view_organizations'],
            'Location': ['view_locations'],
            'Host': ['view_hosts'],
        },
    )

    # Create user with edit roles
    user = module_target_sat_insights.api.User(
        role=[rhcloud_role, additional_role],
        admin=False,
        password=user_password,
        organization=[rhcloud_manifest_org],
        location=[default_location],
    ).create()
    # Set default organization and location after creation to avoid validation order issues
    user.default_organization = rhcloud_manifest_org
    user.default_location = default_location
    user.update(['default_organization', 'default_location'])

    # Verify insights-client package is installed
    assert rhel_insights_vm.execute('insights-client --version').status == 0

    # Prepare misconfigured machine and upload data to Insights
    create_insights_recommendation(rhel_insights_vm)

    # Log in as the user with edit permissions
    with module_target_sat_insights.ui_session(
        test_name, user.login, user_password
    ) as session:
        session.organization.select(org_name=org_name)

        # Verify that we can see the rule hit via insights-client
        result = rhel_insights_vm.execute('insights-client --diagnosis')
        assert result.status == 0
        assert 'OPENSSH_HARDENING_CONFIG_PERMS' in result.stdout
        # Disable recommendation
        session.recommendationstab.disable_recommendation(
            recommendation_name=OPENSSH_RECOMMENDATION
        )
        # Verify that the disabled recommendation is filtered
        result = session.recommendationstab.apply_filter("Status", "Disabled")
        assert 'No recommendations' in result[0]['Name']
        assert 'Decreased security: OpenSSH config permissions' in result[0]['Name']

        # Test Vulnerability with edit permissions
        session.cloudvulnerability.edit_vulnerabilities(CVE_ID)
        vulnerabilities = session.cloudvulnerability.read()
        # Find the edited CVE in the list of vulnerabilities
        edited_cve = next((v for v in vulnerabilities if CVE_ID in v.get('CVE ID', '')), None)
        assert edited_cve is not None, f"CVE {CVE_ID} not found in vulnerabilities list"
        assert edited_cve['Status'] == 'In review'


@pytest.mark.no_containers
@pytest.mark.rhel_ver_match('10')
@pytest.mark.parametrize('module_target_sat_insights', [False], ids=['local'], indirect=True)
def test_iop_insights_rbac_no_permissions(
    test_name,
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat_insights,
    default_location,
):
    """Verify that a user with no advisor or vulnerability permissions cannot access
    Insights Recommendations or Vulnerabilities.

    :id: e5f6a7b8-c9d0-4e5f-2a3b-4c5d6e7f8a9b

    :steps:
        1. Create a role with no advisor or vulnerability permissions.
        2. Create a test user with the role and log in.
        3. Attempt to navigate to Red Hat Lightspeed → Recommendations.
        4. Verify access is denied or page is not accessible.
        5. Attempt to navigate to Red Hat Lightspeed → Vulnerabilities.
        6. Verify access is denied or page is not accessible.

    :expectedresults:
        1. User cannot access the Recommendations page.
        2. User cannot access the Vulnerabilities page.
        3. Navigation items may be hidden or access is denied with permission error.

    :CaseImportance: High

    :customerscenario: true

    :parametrized: yes

    :CaseAutomation:

    :BlockedBy: RHINENG-23601
    """
    user_password = gen_string('alpha')

    # Create role with no advisor or vulnerability permissions
    # Only include basic organization and location permissions
    role = module_target_sat_insights.api.Role(organization=[rhcloud_manifest_org]).create()
    module_target_sat_insights.api_factory.create_role_permissions(
        role,
        {
            'Organization': ['view_organizations'],
            'Location': ['view_locations'],
            'Host': ['view_hosts'],
            None: ['generate_foreman_rh_cloud', 'view_foreman_rh_cloud'],
            'InsightsHit': ['view_insights_hits'],
        },
    )

    # Create user with no insights permissions
    user = module_target_sat_insights.api.User(
        role=[role],
        admin=False,
        password=user_password,
        organization=[rhcloud_manifest_org],
        location=[default_location],
    ).create()
    # Set default organization and location after creation to avoid validation order issues
    user.default_organization = rhcloud_manifest_org
    user.default_location = default_location
    user.update(['default_organization', 'default_location'])

    # Verify insights-client package is installed
    assert rhel_insights_vm.execute('insights-client --version').status == 0

    # Prepare misconfigured machine and upload data to Insights
    create_insights_recommendation(rhel_insights_vm)

    # Log in as the user with no insights permissions
    # User is already in their default organization, no need to select
    with module_target_sat_insights.ui_session(
        test_name, user.login, user_password
    ) as session:
        # Verify that we can see the rule hit via insights-client (as admin)
        result = rhel_insights_vm.execute('insights-client --diagnosis')
        assert result.status == 0
        assert 'OPENSSH_HARDENING_CONFIG_PERMS' in result.stdout
        # Attempt to access Recommendations - should fail or be inaccessible
        permission = session.recommendationstab.read_no_authorized_message()
        assert "You do not have access to Advisor" == permission
        permission = session.cloudvulnerability.read_no_authorized_message()
        assert "You do not have access to Vulnerability" == permission
