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
from fabric.api import run
from nailgun import entities
from upgrade_tests.helpers.scenarios import create_dict
from upgrade_tests.helpers.scenarios import get_entity_data


class TestScenarioDBseedHostMismatch:
    """This test scenenario veryfies the

    Test Steps:

        1. Before Satellite upgrade
        2. Create a New Organization and Location
        3. Create another Organization in another Location
        4. Create a content host in the first Location
        5. Ensure the host's org is in the first location
        6. Edit the host information using rake console to be in the second location
        7. Ensure the host is not in the same Location as its Org
        8. Upgrade Satellite
        9. Ensure upgrade succeeds

    BZ: 2043705, 2028786, 2019467
    """

    @pytest.mark.pre_upgrade
    def test_pre_db_seed_host_mismatch(self, default_sat, rhel7_contenthost):
        """

        :id:

        :steps:
            1. Create an Organizaiton1 and Location
            2. Create another Organization2
            3. Create a content host on Organization1
            4. Use rake console to edit the content host to Org2
            5. Ensure the taxonomy between the content host and Location is broken

        :expectedresults:
            1. The content host should be in Organization2 but not Location

        :BZ: 2043705, 2028786, 2019467



        :customerscenario: true
        """
        org = default_sat.Organization.create()
        loc = default_sat.Location.create(organization=org)
        org2 = default_sat.Organization.create()

        rhel7_contenthost.install_capsule_katello_ca(capsule=self.proxy_name)
        rhel7_contenthost.register_contenthost(org=org, lce='Library')

        chost = default_sat.Host().search(query={'search': f'name="{rhel7_contenthost.hostname}"'})

        assert chost[0]['organization'] == org.name
        assert chost[0]['organization'] != org2.name
        assert chost[0]['location'] == loc.name

        rake_host = f"host = Host.where(:name => '{chost.name}')"
        rake_organization = f'; host.organization_id=${org2.id}'
        rake_host_save = '; host.save!'
        result = run(
            f"echo '{rake_host}{rake_organization}{rake_host_save}' | foreman-rake console"
        )

        assert 'true' in result
        assert chost['organization'] == org2.name

        global_dict = {self.__class__.__name__: {'client_name': rhel7_contenthost.hostname}}
        create_dict(global_dict)

        # do the upgrade

    @pytest.mark.post_upgrade(depend_on=test_pre_db_seed_host_mismatch)
    def test_post_db_seed_host_mismatch(self, default_sat):
        """"""

        # ensure the upgrade succeeds and is in org 1
