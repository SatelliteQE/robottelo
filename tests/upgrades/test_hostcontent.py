"""Test Hosts Content related Upgrade Scenario's

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
from upgrade_tests.helpers.scenarios import create_dict
from upgrade_tests.helpers.scenarios import get_entity_data


class TestScenarioDBseedHostMismatch:
    """This test scenenario veryfies that the upgrade succeeds when inconsistencies exist
    within the database.

    Test Steps:

        1. Before Satellite upgrade
        2. Create a New Organization and Location
        3. Create a Content Host in the Org
        4. Ensure the Org is not in the Location
        4. Assign the content host to the Location
        7. Ensure the host is not in the same Location as its Org
        8. Upgrade Satellite
        9. Ensure upgrade succeeds

    BZ: 2043705, 2028786, 2019467
    """

    @pytest.mark.pre_upgrade
    def test_pre_db_seed_host_mismatch(self, target_sat, rhel7_contenthost):
        """

        :id:

        :steps:
            1. Create a Location
            2. Create an Org and ensure the Org is not in the Location
            3. Create a content host on Org
            4. Use rake console to assign the Content Host to the Location
            5. Ensure the taxonomy between the Content Host, Org and Location is broken
            6. Do the upgrade

        :expectedresults:
            1. The Content Hosts is assigned to Location but Org is not

        :BZ: 2043705, 2028786, 2019467

        :customerscenario: true
        """
        org = target_sat.api.Organization().create()
        loc = target_sat.api.Location().create()

        rhel7_contenthost.install_katello_ca(target_sat)
        rhel7_contenthost.register_contenthost(org=org.label, lce='Library')

        chost = entities.Host().search(query={'search': f'name="{rhel7_contenthost.hostname}"'})

        assert chost[0].organization.id == org.id

        # Now we need to break the taxonomy between chost, org and location
        rake_host = f"host = ::Host.find({chost[0].id})"
        rake_organization = f"; host.location_id={loc.id}"
        rake_host_save = "; host.save!"
        result = target_sat.run(
            f"echo '{rake_host}{rake_organization}{rake_host_save}' | foreman-rake console"
        )

        assert 'true' in result.stdout
        chost = entities.Host().search(query={'search': f'name="{rhel7_contenthost.hostname}"'})
        assert chost[0].location.id == loc.id

        global_dict = {
            self.__class__.__name__: {
                'client_name': rhel7_contenthost.hostname,
                'organization_id': org.id,
                'location_id': loc.id,
            }
        }

        create_dict(global_dict)


    @pytest.mark.post_upgrade(depend_on=test_pre_db_seed_host_mismatch)
    def test_post_db_seed_host_mismatch(self, target_sat):
        """"""
        chostname = get_entity_data(self.__class__.__name__)['client_name']
        org_id = get_entity_data(self.__class__.__name__)['organization_id']
        loc_id = get_entity_data(self.__class__.__name__)['location_id']
        chost = entities.Host(name=chostname)

        assert org_id == chost[0].organization.id
        assert loc_id == chost[0].location.id
        # ensure the upgrade succeeds and is in org/location
