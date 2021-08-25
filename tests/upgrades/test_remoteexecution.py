"""Test for Remote Execution related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: RemoteExecution

:Assignee: pondrejk

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest
from nailgun import entities
from upgrade_tests import post_upgrade
from upgrade_tests import pre_upgrade
from upgrade_tests.helpers.scenarios import create_dict
from upgrade_tests.helpers.scenarios import get_entity_data

from robottelo.config import settings
from robottelo.hosts import Capsule


@pytest.fixture(scope='class')
def compute_resource_setup(self, default_org):
    self.libvirt_vm = settings.compute_resources.libvirt_hostname
    self.default_org_id = default_org.id
    self.org = default_org
    self.bridge = settings.vlan_networking.bridge
    self.subnet = settings.vlan_networking.subnet
    self.gateway = settings.vlan_networking.gateway
    self.netmask = settings.vlan_networking.netmask
    self.vm_domain_name = settings.upgrade.vm_domain
    self.vm_domain = entities.Domain().search(query={'search': f'name="{self.vm_domain_name}"'})
    self.proxy_name = settings.upgrade.capsule_hostname


# TODO Mark with infra markers from #8391
@pytest.mark.skipif((not settings.vlan_networking), reason='vlan_networking required')
@pytest.mark.skipif(
    (not settings.compute_resources.libvirt_hostname),
    reason='compute_resources.libvirt_hostname required',
)
@pytest.mark.skipif((not settings.upgrade.vm_domain), reason='upgrade.vm_domain required')
class TestScenarioREXCapsule:
    """Test Remote Execution job created before migration runs successfully
    post migration on a client registered with external capsule.

        Test Steps:

        1. Before Satellite upgrade:
           a. Create Content host.
           b. Create a Subnet on Satellite.
           c. Install katello-ca on content host.
           d. Register content host to Satellite.
           e. add_ssh_key of external capsule on content host.
           f. run a REX job on content host.
        2. Upgrade satellite/capsule.
        3. Run a rex Job again with same content host.
        4. Check if REX job still getting success.
    """

    @pre_upgrade
    def test_pre_scenario_remoteexecution_external_capsule(
        self, request, default_location, rhel7_contenthost
    ):
        """Run REX job on client registered with external capsule

        :id: preupgrade-261dd2aa-be01-4c34-b877-54b8ee346561

        :steps:
            1. Create Subnet.
            2. Create Content host.
            3. Install katello-ca package and register to Satellite host.
            4. add rex ssh_key of external capsule on content host.
            5. run the REX job on client vm.

        :expectedresults:
            1. Content host should create with pre-required details.
            2. REX job should run on it.
        """
        sn = entities.Subnet(
            domain=self.vm_domain,
            gateway=self.gateway,
            ipam='DHCP',
            location=[default_location.id],
            mask=self.netmask,
            network=self.subnet,
            organization=[self.org.id],
            remote_execution_proxy=[entities.SmartProxy(id=2)],
        ).create()
        rhel7_contenthost.install_capsule_katello_ca(capsule=self.proxy_name)
        rhel7_contenthost.register_contenthost(org=self.org.label, lce='Library')
        capsule = Capsule(self.proxy_name)
        rhel7_contenthost.add_rex_key(satellite=capsule)
        host = entities.Host().search(query={'search': f'name="{rhel7_contenthost.hostname}"'})
        host[0].subnet = sn
        host[0].update(['subnet'])
        job = entities.JobInvocation().run(
            data={
                'job_template_id': 89,
                'inputs': {'command': 'ls'},
                'targeting_type': 'static_query',
                'search_query': f'name = {rhel7_contenthost.hostname}',
            }
        )
        assert job['output']['success_count'] == 1
        global_dict = {self.__class__.__name__: {'client_name': rhel7_contenthost.hostname}}
        create_dict(global_dict)

    @post_upgrade(depend_on=test_pre_scenario_remoteexecution_external_capsule)
    def test_post_scenario_remoteexecution_external_capsule(self):
        """Run a REX job on pre-upgrade created client registered
        with external capsule.

        :id: postupgrade-00ed2a25-b0bd-446f-a3fc-09149c57fe94

        :steps:
            1. Run a REX job on content host.

        :expectedresults:
            1. The job should successfully executed on pre-upgrade created client.
        """
        client_name = get_entity_data(self.__class__.__name__)['client_name']
        job = entities.JobInvocation().run(
            data={
                'job_template_id': 89,
                'inputs': {'command': 'ls'},
                'targeting_type': 'static_query',
                'search_query': f'name = {client_name}',
            }
        )
        assert job['output']['success_count'] == 1


# TODO Mark with infra markers from #8391
@pytest.mark.skipif((not settings.vlan_networking), reason='vlan_networking required')
@pytest.mark.skipif(
    (not settings.compute_resources.libvirt_hostname),
    reason='compute_resources.libvirt_hostname required',
)
@pytest.mark.skipif((not settings.upgrade.vm_domain), reason='upgrade.vm_domain required')
class TestScenarioREXSatellite:
    """Test Remote Execution job created before migration runs successfully
    post migration on a client registered with Satellite.

        Test Steps:

        1. Before Satellite upgrade:
        2. Create Content host.
        3. Create a Subnet on Satellite.
        4. Install katello-ca on content host.
        5. Register content host to Satellite.
        6. Add_ssh_key of Satellite on content host.
        7. Run a REX job on content host.
        8. Upgrade satellite/capsule.
        9. Run a rex Job again with same content host.
        10. Check if REX job still getting success.
    """

    @pre_upgrade
    def test_pre_scenario_remoteexecution_satellite(
        self, request, compute_resource_setup, default_location, rhel7_contenthost, default_sat
    ):
        """Run REX job on client registered with Satellite

        :id: preupgrade-3f338475-fa69-43ef-ac86-f00f4d324b33

        :steps:
            1. Create Subnet.
            2. Create Content host.
            3. Install katello-ca package and register to Satellite host.
            4. Add rex ssh_key of Satellite on content host.
            5. Run the REX job on client vm.

        :expectedresults:
            1. It should create with pre-required details.
            2. REX job should run on it.
        """
        sn = entities.Subnet(
            domain=self.vm_domain,
            gateway=self.gateway,
            ipam='DHCP',
            location=[default_location.id],
            mask=self.netmask,
            network=self.subnet,
            organization=[self.org.id],
            remote_execution_proxy=[entities.SmartProxy(id=1)],
        ).create()
        rhel7_contenthost.configure_rex(satellite=default_sat, org=self.org, by_ip=False)
        host = rhel7_contenthost.nailgun_host
        host[0].subnet = sn
        host[0].update(['subnet'])
        job = entities.JobInvocation().run(
            data={
                'job_template_id': 89,
                'inputs': {'command': 'ls'},
                'targeting_type': 'static_query',
                'search_query': f'name = {rhel7_contenthost.hostname}',
            }
        )
        assert job['output']['success_count'] == 1
        global_dict = {self.__class__.__name__: {'client_name': rhel7_contenthost.hostname}}
        create_dict(global_dict)

    @post_upgrade(depend_on=test_pre_scenario_remoteexecution_satellite)
    def test_post_scenario_remoteexecution_satellite(self):
        """Run a REX job on pre-upgrade created client registered
        with Satellite.

        :id: postupgrade-ad3b1564-d3e6-4ada-9337-3a6ee6863bae

        :steps:
            1. Run a REX job on content host.

        :expectedresults:
            1. The job should successfully executed on pre-upgrade created client.
        """
        client_name = get_entity_data(self.__class__.__name__)['client_name']
        job = entities.JobInvocation().run(
            data={
                'job_template_id': 89,
                'inputs': {'command': 'ls'},
                'targeting_type': 'static_query',
                'search_query': f'name = {client_name}',
            }
        )
        assert job['output']['success_count'] == 1
