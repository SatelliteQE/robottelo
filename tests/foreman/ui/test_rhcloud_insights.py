"""Tests for RH Cloud - Inventory

:Requirement: RH Cloud - Inventory

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: RH Cloud - Inventory

:Assignee: jpathan

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
from datetime import datetime
from datetime import timedelta

import pytest

from robottelo.api.utils import wait_for_tasks
from robottelo.config import settings


@pytest.mark.run_in_one_thread
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
        4. Run remediation for a recommendation against rhel8 host.
        5. Assert that job completed successfully.
        6. Sync Insights recommendations.
        7. Search for previously remediated issue.

    :expectedresults:
        1. Insights recommendation is listed for host.
        2. Remediation job finished successfully.
        3. Remediated Insights recommendation is not listed.

    :CaseAutomation: Automated
    """
    org, ak = organization_ak_setup
    # Use recommendation other than dnf one till BZ#1976754
    query = 'Insights Client Core egg file'
    job_query = (
        f'Remote action: Insights remediations for selected issues on {rhel8_insights_vm.hostname}'
    )
    with session:
        session.organization.select(org_name=org.name)
        timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.save_token_sync_hits(settings.rh_cloud.token)
        wait_for_tasks(
            search_query=f'Insights full sync and started_at >= "{timestamp}"',
            search_rate=15,
            max_tries=10,
        )
        result = session.cloudinsights.search(query)[0]
        assert result['Hostname'] == rhel8_insights_vm.hostname
        assert (
            result['Recommendation']
            == 'System is not able to get the latest recommendations and may miss bug '
            'fixes when the Insights Client Core egg file is outdated'
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
        timestamp = (datetime.utcnow() - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M')
        session.cloudinsights.sync_hits()
        wait_for_tasks(
            search_query=f'Insights full sync and started_at >= "{timestamp}"',
            search_rate=15,
            max_tries=10,
        )
        # Workaround for alert message causing search to fail.
        session.browser.refresh()
        assert not session.cloudinsights.search(query)
