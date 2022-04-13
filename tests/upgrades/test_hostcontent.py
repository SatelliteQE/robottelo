"""Test db:seed related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Host-Content

:Assignee: spusater

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities


class TestScenarioDBseedHostMismatch:
    """This test scenenario veryfies the

    Test Steps:

        1. Before Satellite upgrade
        2. Create a New Organization and Location
        3. Create another Organization in another Location
        4. Create a content host in the first Location
        5. Ensure the host's org is not in the first location
        6. Edit the host information using rake console
        7. Ensure the host is not in the same Location as its Org
        8. Upgrade Satellite
        9. Ensure upgrade succeeds

    BZ: 2043705
    """

    @pytest.fixture(scope='function')
    def setup_host_mismatch(self, default_sat):
        """Create the organizaitons and locations needed for the contest hosts"""

        org = default_sat.api.Organization().create()
        loc = default_sat.api.Location(organization=[org]).create()
        lce = default_sat.api.LifecycleEnvironment(organization=org).create()

        org2 = default_sat.api.Organization().create()
        loc2 = default_sat.api.Location(organization=[org2]).create()

        # chost = default_sat.api.
        # assert chost in loc1, not in loc2
        # assert chost in org1, not in loc2

    @pytest.mark.post_upgrade()
    def test_db_seed_host_mismatch(self):
        """

        :id:

        :steps:
            1. Create an Organizaiton1 and Location1
            2. Create another Organization2 in another Location2
            3. Create a content host on Organization1 but not in Location2

        :expectedresults:
            1. The Content Host exists on Organization but not Location

        :BZ: 2043705

        :customerscenario: true
        """
