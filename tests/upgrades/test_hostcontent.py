"""Test Hosts-Content related Upgrade Scenarios

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Host-Content

:Team: Phoenix

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest


class TestScenarioDBseedHostMismatch:
    """This test scenario verifies that the upgrade succeeds even when inconsistencies exist
    in the database between Organization, Location and Content Host.

    Test Steps:

        1. Before Satellite upgrade
        2. Create a New Organization and Location
        3. Create a Content Host in the Organization
        4. Ensure the Location is not in the Org
        5. Assign the Content Host to the Location using the rake console
        6. Ensure the Host is in both, but the Location is not in Org, creating a mismatch
        7. Upgrade Satellite
        8. Ensure upgrade succeeds

    BZ: 2043705, 2028786, 2019467
    """

    @pytest.mark.pre_upgrade
    def test_pre_db_seed_host_mismatch(
        self, target_sat, function_org, function_location, rhel7_contenthost_module, save_test_data
    ):
        """
        :id: preupgrade-28861b9f-8abd-4efc-bfd5-40b7e825a941

        :steps:
            1. Create a Location
            2. Create an Org and ensure the Location is not in the Org
            3. Create a Content Host on Org
            4. Use rake console to assign the Content Host to the Location
            5. Ensure the mismatch is created for Content Host when Location is not in the Org
            6. Do the upgrade

        :expectedresults:
            1. The Content Host is assigned to both Location and Org, but Location is not in Org

        :BZ: 2043705, 2028786, 2019467

        :customerscenario: true
        """
        rhel7_contenthost_module.install_katello_ca(target_sat)
        rhel7_contenthost_module.register_contenthost(org=function_org.label, lce='Library')

        assert rhel7_contenthost_module.nailgun_host.organization.id == function_org.id

        # Now we need to break the taxonomy between chost, org and location
        rake_host = f"host = ::Host.find({rhel7_contenthost_module.nailgun_host.id})"
        rake_location = f"; host.location_id={function_location.id}"
        rake_host_save = "; host.save!"
        result = target_sat.run(
            f"echo '{rake_host}{rake_location}{rake_host_save}' | foreman-rake console"
        )

        assert 'true' in result.stdout
        assert rhel7_contenthost_module.nailgun_host.location.id == function_location.id

        save_test_data(
            {
                'client_name': rhel7_contenthost_module.hostname,
                'organization_id': function_org.id,
                'location_id': function_location.id,
            }
        )

    @pytest.mark.post_upgrade(depend_on=test_pre_db_seed_host_mismatch)
    def test_post_db_seed_host_mismatch(self, target_sat, pre_upgrade_data):
        """
        :id: postupgrade-28861b9f-8abd-4efc-bfd5-40b7e825a941

        :steps:
            1. After the upgrade finishes ensure the content host data is unchanged

        :expectedresults:
            1. The upgrade succeeds and content host exists

        :BZ: 2043705, 2028786, 2019467

        :customerscenario: true
        """
        chostname = pre_upgrade_data['client_name']
        org_id = pre_upgrade_data['organization_id']
        loc_id = pre_upgrade_data['location_id']
        chost = target_sat.api.Host().search(query={'search': chostname})

        assert org_id == chost[0].organization.id
        assert loc_id == chost[0].location.id
