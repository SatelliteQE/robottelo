"""Tests for RH Cloud - Inventory

:Requirement: RH Cloud - Inventory

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: RHCloud-Inventory

:Assignee: jpathan

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
from datetime import datetime

import pytest

from robottelo.api.utils import wait_for_tasks
from robottelo.config import settings


@pytest.mark.run_in_one_thread
@pytest.mark.tier3
def test_rhcloud_insights_e2e(
    session,
    rhel8_insights_vm,
    fixable_rhel8_vm,
    organization_ak_setup,
    enable_lab_features,
    unset_rh_cloud_token,
):
    """Synchronize hits data from cloud, verify it is displayed in Satellite and run remediation.

    :id: d952e83c-3faf-4299-a048-2eb6ccb8c9c2

    :Steps:
        1. Prepare misconfigured machine and upload its data to Insights.
        2. Add Cloud API key in Satellite.
        3. In Satellite UI, Configure -> Insights -> Add RH Cloud token and syns recommendations.
        4. Run remediation for dnf.conf recommendation against rhel8 host.
        5. Assert that job completed successfully.
        6. Sync Insights recommendations.
        7. Search for previously remediated issue.

    :expectedresults:
        1. Insights recommendation related to dnf.conf issue is listed for misconfigured machine.
        2. Remediation job finished successfully.
        3. Insights recommendation related to dnf.conf issue is not listed.

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    query = 'dnf.conf'
    job_query = (
        f'Remote action: Insights remediations for selected issues on {rhel8_insights_vm.hostname}'
    )
    with session:
        session.organization.select(org_name=org.name)
        session.cloudinsights.save_token_sync_hits(settings.rh_cloud.token)
        # This is a workaround for BZ#1983575. Remove following two code lines once BZ is fixed.
        session.browser.refresh()
        session.cloudinsights.sync_hits()

        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        wait_for_tasks(
            search_query=f'Insights full sync and started_at >= "{timestamp}"',
            search_rate=15,
            max_tries=10,
        )
        # Workaround for alert message causing search to fail. See airgun issue 584.
        session.browser.refresh()
        result = session.cloudinsights.search(query)[0]
        assert result['Hostname'] == rhel8_insights_vm.hostname
        assert (
            result['Recommendation'] == 'The dnf installs lower versions of packages when the '
            '"best" option is not present in the /etc/dnf/dnf.conf'
        )
        session.cloudinsights.remediate(query)
        wait_for_tasks(
            search_query=f'{job_query} and started_at >= "{timestamp}"',
            search_rate=15,
            max_tries=10,
        )
        job_invocation = wait_for_tasks(
            search_query=f'{job_query} and started_at >= "{timestamp}"',
            search_rate=15,
            max_tries=10,
        )
        assert job_invocation[0].result == 'success'
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.sync_hits()
        wait_for_tasks(
            search_query=f'Insights full sync and started_at >= "{timestamp}"',
            search_rate=15,
            max_tries=10,
        )
        # Workaround for alert message causing search to fail. See airgun issue 584.
        session.browser.refresh()
        assert not session.cloudinsights.search(query)
