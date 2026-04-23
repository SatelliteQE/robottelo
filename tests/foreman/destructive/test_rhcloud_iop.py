"""Destructive Tests for RH Cloud - IOP

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: Insights-Advisor

:Team: Proton

:CaseImportance: High
"""

import pytest

from robottelo.config import settings
from robottelo.constants import OPENSSH_RECOMMENDATION
from tests.foreman.ui.test_rhcloud_insights import (
    create_insights_vulnerability as create_insights_recommendation,
)


@pytest.mark.no_containers
@pytest.mark.rhel_ver_list([settings.content_host.default_rhel_version])
def test_re_register_after_enabling_iop(
    rhel_insights_vm,
    rhcloud_manifest_org,
    module_target_sat_insights,
):
    """
    Verify that a remediation job can be run successfully on a host that was originally registered
    to hosted Insights after enabling IoP on Satellite and re-registering the host to IoP.

    :id: bf626832-96da-4a75-ad55-c57cbc226efe

    :steps:
        1. Register a host to hosted Insights via Satellite.
        2. Enable IoP on Satellite.
        3. Re-run `insights-client --register` on the host.
        4. Create a recommendation on the host.
        5. Attempt to run a remediation job for the recommendation.

    :expectedresults:
        The remediation job runs successfully on the host.
    """
    assert rhel_insights_vm.execute('insights-client --test-connection').status == 0
    module_target_sat_insights.configure_iop()
    assert rhel_insights_vm.execute('insights-client --register').status == 0
    create_insights_recommendation(rhel_insights_vm)

    with module_target_sat_insights.ui_session() as session:
        session.organization.select(org_name=rhcloud_manifest_org.name)

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
