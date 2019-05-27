"""Test for Remote Execution related Upgrade Scenario's

:Requirement: Upgraded Satellite

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import os

from nailgun import entities
from robottelo.constants import DEFAULT_LOC, DEFAULT_ORG, DISTRO_RHEL7
from robottelo.helpers import add_remote_execution_ssh_key
from robottelo.vm import VirtualMachine
from robottelo.test import APITestCase
from upgrade_tests import post_upgrade, pre_upgrade
from upgrade_tests.helpers.scenarios import create_dict, get_entity_data


class Scenario_remoteexecution_external_capsule(APITestCase):
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

    @classmethod
    def setUpClass(cls):
        cls.libvirt_vm = os.environ.get('LIBVIRT_HOSTNAME')
        cls.default_org_id = entities.Organization().search(
            query={'search': 'name="{}"'.format(DEFAULT_ORG)})[0].id
        cls.org = entities.Organization(id=cls.default_org_id).read()
        cls.bridge = os.environ.get('BRIDGE')
        cls.subnet = os.environ.get('SUBNET')
        cls.gateway = os.environ.get('GATEWAY')
        cls.netmask = os.environ.get('NETMASK')
        cls.vm_domain_name = os.environ.get('VM_DOMAIN')
        cls.vm_domain = entities.Domain().search(query={'search': 'name="{}"'
                                                 .format(cls.vm_domain_name)})
        cls.proxy_name = os.environ.get('RHEV_CAP_HOST')

    def _vm_cleanup(self, hostname=None):
        """ Cleanup the VM from provisioning server

        :param str hostname: The content host hostname
        """
        if hostname:
            vm = VirtualMachine(
                hostname=hostname,
                target_image=hostname,
                provisioning_server=self.libvirt_vm,
                distro=DISTRO_RHEL7,
                )
            vm._created = True
            vm.destroy()

    @pre_upgrade
    def test_pre_scenario_remoteexecution_external_capsule(self):
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
        try:
            default_loc_id = entities.Location().search(
                query={'search': 'name="{}"'.format(DEFAULT_LOC)})[0].id
            sn = entities.Subnet(
                domain=self.vm_domain,
                gateway=self.gateway,
                ipam='DHCP',
                location=[default_loc_id],
                mask=self.netmask,
                network=self.subnet,
                organization=[self.org.id],
                remote_execution_proxy=[entities.SmartProxy(id=2)],
            ).create()
            client = VirtualMachine(
                distro=DISTRO_RHEL7,
                provisioning_server=self.libvirt_vm,
                bridge=self.bridge)
            client.create()
            client.install_capsule_katello_ca(capsule=self.proxy_name)
            client.register_contenthost(org=self.org.label, lce='Library')
            add_remote_execution_ssh_key(hostname=client.ip_addr,
                                         proxy_hostname=self.proxy_name)
            host = entities.Host().search(
                query={'search': 'name="{}"'.format(client.hostname)})
            host[0].subnet = sn
            host[0].update(['subnet'])
            job = entities.JobInvocation().run(data={
                'job_template_id': 89, 'inputs': {'command': "ls"},
                'targeting_type': 'static_query', 'search_query': "name = {0}"
                .format(client.hostname)})
            self.assertEqual(job['output']['success_count'], 1)
            global_dict = {
                self.__class__.__name__: {'client_name': client.hostname}
            }
            create_dict(global_dict)
        except Exception as exp:
            if client._created:
                self._vm_cleanup(hostname=client.hostname)
            raise Exception(exp)

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
        job = entities.JobInvocation().run(data={
            'job_template_id': 89, 'inputs': {'command': "ls"},
            'targeting_type': 'static_query', 'search_query': "name = {0}".format(client_name)})
        self.assertEqual(job['output']['success_count'], 1)
        self._vm_cleanup(hostname=client_name)


class Scenario_remoteexecution_satellite(APITestCase):
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

    @classmethod
    def setUpClass(cls):
        cls.libvirt_vm = os.environ.get('LIBVIRT_HOSTNAME')
        cls.default_org_id = entities.Organization().search(
            query={'search': 'name="{}"'.format(DEFAULT_ORG)})[0].id
        cls.org = entities.Organization(id=cls.default_org_id).read()
        cls.bridge = os.environ.get('BRIDGE')
        cls.subnet = os.environ.get('SUBNET')
        cls.gateway = os.environ.get('GATEWAY')
        cls.netmask = os.environ.get('NETMASK')
        cls.vm_domain_name = os.environ.get('VM_DOMAIN')
        cls.vm_domain = entities.Domain().search(query={'search': 'name="{}"'
                                                 .format(cls.vm_domain_name)})
        cls.proxy_name = os.environ.get('RHEV_SAT_HOST')

    def _vm_cleanup(self, hostname=None):
        """ Cleanup the VM from provisioning server

        :param str hostname: The content host hostname
        """
        if hostname:
            vm = VirtualMachine(
                hostname=hostname,
                target_image=hostname,
                provisioning_server=self.libvirt_vm,
                distro=DISTRO_RHEL7,
                )
            vm._created = True
            vm.destroy()

    @pre_upgrade
    def test_pre_scenario_remoteexecution_satellite(self):
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
        try:
            default_loc_id = entities.Location().search(
                query={'search': 'name="{}"'.format(DEFAULT_LOC)})[0].id
            sn = entities.Subnet(
                domain=self.vm_domain,
                gateway=self.gateway,
                ipam='DHCP',
                location=[default_loc_id],
                mask=self.netmask,
                network=self.subnet,
                organization=[self.org.id],
                remote_execution_proxy=[entities.SmartProxy(id=1)],
            ).create()
            client = VirtualMachine(
                distro=DISTRO_RHEL7,
                provisioning_server=self.libvirt_vm,
                bridge=self.bridge)
            client.create()
            client.install_katello_ca()
            client.register_contenthost(org=self.org.label, lce='Library')
            add_remote_execution_ssh_key(hostname=client.ip_addr)
            host = entities.Host().search(
                query={'search': 'name="{}"'.format(client.hostname)})
            host[0].subnet = sn
            host[0].update(['subnet'])
            job = entities.JobInvocation().run(data={
                'job_template_id': 89, 'inputs': {'command': "ls"},
                'targeting_type': 'static_query', 'search_query': "name = {0}"
                .format(client.hostname)})
            self.assertEqual(job['output']['success_count'], 1)
            global_dict = {
                self.__class__.__name__: {'client_name': client.hostname}
            }
            create_dict(global_dict)
        except Exception as exp:
            if client._created:
                self._vm_cleanup(hostname=client.hostname)
            raise Exception(exp)

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
        job = entities.JobInvocation().run(data={
            'job_template_id': 89, 'inputs': {'command': "ls"},
            'targeting_type': 'static_query', 'search_query': "name = {0}".format(client_name)})
        self.assertEqual(job['output']['success_count'], 1)
        self._vm_cleanup(hostname=client_name)
