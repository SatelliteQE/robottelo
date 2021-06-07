"""Tests for RH Cloud - Insights

:Requirement: RH Cloud - Insights

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: RHCloud-Insights

:Assignee: jpathan

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest

from robottelo.config import settings


@pytest.mark.tier3
def test_rhcloud_insights_e2e(
    session, rhel8_insights_vm, fixable_rhel8_vm, organization_ak_setup, unset_set_cloud_token
):
    """Synchronize hits data from cloud, verify it is displayed in Satellite and run remediation.

    :id: d952e83c-3faf-4299-a048-2eb6ccb8c9c2

    :Steps:
        1. Prepare misconfigured machine and upload its data to Insights.
        2. Add Cloud API key in Satellite.
        3. In Satellite UI, Configure -> Insights -> Add RH Cloud token and syns recommendations.
        4. Run remediation for dnf.conf recommendation against rhel8 host.
        5. Assert that job completed successfully.
        6. Upload insights data again.
        7. Sync Insights recommendations.
        8. Search for previously remediated issue.

    :expectedresults:
        1. Insights recommendation related to dnf.conf issue is listed for misconfigured machine.
        2. Remediation job finished successfully.
        3. Insights recommendation related to dnf.conf issue is not listed.

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    query = 'dnf.conf'
    with session:
        session.organization.select(org_name=org.name)
        # uncomment once https://bugzilla.redhat.com/show_bug.cgi?id=1965901 is fixed
        # session.cloudinsights.save_token_sync_hits(settings.rh_cloud.token)
        result = session.cloudinsights.search(query)[0]
        assert result['Hostname'] == rhel8_insights_vm.hostname
        assert (
            result['Recommendation'] == 'The dnf installs lower versions of packages when the '
            '"best" option is not present in the /etc/dnf/dnf.conf'
        )
        session.cloudinsights.remediate(query)
        session.jobinvocation.wait_job_invocation_state(
            entity_name='Insights remediations for selected issues',
            host_name=rhel8_insights_vm.hostname,
        )
        status = session.jobinvocation.read(
            entity_name='Insights remediations for selected issues',
            host_name=rhel8_insights_vm.hostname,
        )
        assert status['overview']['hosts_table'][0]['Status'] == 'success'
        rhel8_insights_vm.run('insights-client')
        session.cloudinsights.sync_hits()
        # Workaround for https://bugzilla.redhat.com/show_bug.cgi?id=1962048
        session.browser.refresh()
        assert not session.cloudinsights.search(query)
