"""Tests for RH Cloud - IOP

:Requirement: RHCloud

:CaseAutomation: Automated

:CaseComponent: RHCloud

:Team: Proton

:CaseImportance: High

"""

import json
from pathlib import Path

from box import Box
import pytest


@pytest.mark.no_containers
@pytest.mark.rhel_ver_list(r'^[\d]+$')
@pytest.mark.parametrize(
    "module_target_sat_insights",
    [False],
    ids=["local"],
    indirect=True,
)
def test_positive_iop_inventory_tags_present(module_target_sat_insights, rhel_insights_vm):
    """Verify that IOP inventory tags exist on a host registered to IOP

    :id: 70dc4438-d27d-477d-80fd-214c4f784c9e

    :steps:

        1. Configure IOP on a Satellite.
        2. Register a host to the Satellite and to IOP.
        3. Assert that the subscription_manager_id, satellite_id, and org_id facts are present in
           the local host details file.

    :expectedresults: The ID facts are present in the local host details file.

    :CaseImportance: Medium

    :verifies: SAT-36164

    :customerscenario: false
    """
    details_path = Path('/var/lib/insights/host-details.json')
    rhel_insights_vm.execute('insights-client')
    host_details = Box(json.loads(rhel_insights_vm.execute(f'cat {details_path}').stdout))
    assert host_details.results[0].subscription_manager_id
    assert host_details.results[0].satellite_id
    assert host_details.results[0].org_id
    assert host_details.results[0].insights_id
