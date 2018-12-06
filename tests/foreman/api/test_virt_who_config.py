"""Test for virt-who configure API

:Requirement: Virtwho-configure

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:CaseAutomation: notautomated

:Upstream: No
"""
from fauxfactory import gen_integer, gen_string, gen_utf8
from nailgun import entities
from robottelo.decorators import run_only_on, stubbed, tier1, tier3, tier4
from robottelo.test import TestCase, APITestCase
from robottelo.config import settings
from robottelo.virt_who_configure import VirtWhoHypervisorConfig, deploy_virt_who_config, make_expected_configfile_section_from_api

class VirtWhoConfigApiTestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(VirtWhoConfigApiTestCase, cls).setUpClass()
        cls.org =  entities.Organization().create()

    @run_only_on('sat')
    @tier1
    def test_positive_config_create(self):
        """ Create a config, deploy it, verify the resulting config files

        :id: 558ebdaa-8e29-47c3-b859-a56f2d28a335

        :steps:
            1. Create a virt-who config object
            2. Deploy config on Satellite Server
            3. Verify the config files

        :expectedresults:
            The config files have the expected config
        """
        vhc_name = "example_config{}".format(gen_integer())
        vhc = entities.VirtWhoConfig(name=vhc_name, organization=self.org,
                                     hypervisor_server=settings.clients.provisioning_server,
                                     satellite_url=settings.server.hostname,
                                     hypervisor_type='libvirt',
                                     hypervisor_username='root',
                                     hypervisor_id='hostname',
                                     hypervisor_password='' ).create()


        deploy_virt_who_config(vhc.id, self.org.id)
        sc = VirtWhoHypervisorConfig(vhc.id)
        expected = make_expected_configfile_section_from_api(vhc)
        errors = sc.verify(expected)
        self.assertEqual(len(errors), 0, errors)





class VirtWhoConfigTestCase(APITestCase):

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_vm_create(self):
        """ Register a vm on virt-who hypervisor

        :id: 701b22b8-fe92-4dd3-8d7d-c7b5efb7281b

        :steps:
            1. Configure Virt-who using Virt-who config plugin
            2. Associate VDC subscription to hypervisor tied to virt-who
            3. Create new VM in a hypervisor
            4. Wait until the next virt-who report comes in.

        :expectedresults:
            Verify the VM is reported to satellite and is tied to the correct
            VDC subscription

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_config_update(self):
        """Update a config, verify it it changed and redploy it

        :id: 6b2cc2c3-959b-468b-9865-0f01decd2249

        :setup:
            Use 2 hypervisors of the same type (HV1 and HV2)

        :steps:
            1. Create a virt-who configuration tied to HV1
            2. Update the config by changing the hostname to HV2
            3. Deploy the configuration.

        :expectedresults:
            Verify the configuration file change and virt-who is configured
            properly.
        """

    @run_only_on('sat')
    @stubbed()
    @tier4
    def test_postive_config_intervals(self):
        """ Verify intervals Intervals

        :id: 7e1bb498-4e63-44e8-be97-83e07601f56d

        :steps:
            1. Create virt-who configuration with reporting interval to 1 hour.
            2. Repeat for each supported interval (1, 2, 4, 8, 12) hours.

        :expectedresults:
            1. Verify Virt-who  interval is correct in config file.
            2. Verify a report is sent every interval

        """


class VirtWhoConfigRoleTestCase(APITestCase):

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_role_manager(self):
        """virt-who Manager allowed functions

        :id: 4164bdde-f532-480c-b41e-747e87cf7d05

        :steps:
            1. Create a user with ONLY the virt-who manager role.

        :expectedresults:
            1. Verify the user can create virt-who configurations
            2. Verify the user can edit an existing virt-who configuration
            3. Verify the user can delete a virt-who configuration
            4. Verify the user can see reporting info via the dashboard widget.


        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_role_manager(self):
        """virt-who Manager disallowed functions

        :id: e93b415a-7442-4f27-9c52-15c72f3e1414

        :steps:
            1. Create a user with ONLY the virt-who manager role.

        :expectedresults:
            1. Verify the user can do no other actions other then those
               in test_positive_role_manager

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_role_reporter(self):
        """ Verify virt-who Reporter role

        :id: 63462338-a6f5-48eb-8b04-433c53882817

        :steps:
            1. Create a user with ONLY the virt-who reporter role.
            2. Configure virt-who with the user, WITHOUT using the
               virt-who config plugin.
            3. Create a vm to cause virt-who to send a report to satellite.

        :expectedresults:
            1. Verify the virt-who server send a report to the satellite.
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_role_reporter(self):
        """Verify virt-who Reporter role

        :id: 7dee0965-9ec4-4d76-a6ae-f2eec1960bac

        :steps:
            1. Create a user with ONLY the virt-who reporter role.

        :expectedresults:
            1. Verify the user can do no other actions other then those
               in test_positive_role_reporter

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_role_viewer(self):
        """ Verify virt-who viewer role

        :id: 43314ae3-6768-44b5-a6bb-ee64ae381cd0

        :steps:
            1. Create a user with ONLY the virt-who Viewer role.

        :expectedresults:
            1. Verify the user can view virt-who configurations.
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_role_viewer(self):
        """ Verify virt-who viewer role

        :id: 6919a748-423e-4843-bafe-eb98b7159c90

        :steps:
            1. Create a user with ONLY the virt-who Viewer role.

        :expectedresults:
            1. Verify the user CANNOT delete or modify virt-who configurations
            2. Verify the user can do no other actions other then those
               in test_positive_role_viewer

        """


class VirtWhoConfigUpgradeTestCase(APITestCase):

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_satellite_upgrade(self):
        """ Satellite upgrade

        :id: 0e301c08-8bef-4bea-a690-d4b0760949e8

        :steps:
            1. Start with a satellite version before the virt-who config
               plugin (eg. 6.2)
            2. Configure virt-who server with virtualization provider (VP1) to
               send reports to the satellite.
            3. Upgrade the satellite to a version with virt-who config plugin.
            4. Configure a new virtualization provider (VP2) with a VDC
               subscription
            5. Using the virt-who plugin, create a configuration for the
               new hypervisor.
            6. Deploy the configuration to the virt-who server
            7. Create a guest on VP1
            8. Create a guest on VP2

        :expectedresults:
            1. verify that that reports on VP1 and VP2 are correct.

        """


class VirtWhoConfigGeneralTestCase(TestCase):

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hypervisors(self):
        """End to End scenarios. For all supported Hypervisors
           (Libvirt, vmware, RHEV, Hyper-V, Xen)

        :id: ce67645a-8435-4e2a-9fd5-c54f2a11c44b

        :steps:
            1. Associate a VDC subscription to the hypervisor host
            2. Create a Virt-who configuration for the hypervisor.
            3. Deploy the virt-who configuration
            4. Create VM1 on the hypervisor
            5. Create activation key with Content view, but DO NOT
               associate subscription.
            6. Register  VM using the activation key.
            7. Wait until the next report comes to the satellite

        :expectedresults:
            1. Verify the VM is report to the Satellite, and the VDC
               subscription is applied to it.
            2. Repeat for each supported hypervisor (Libvirt, vmware, RHEV,
               Hyper-V, Xen)
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_multiple_config_single_instance(self):
        """ Create multiple configs, add to same virt-who instance

        :id: 5d553f0d-4dc8-4ce4-8fa4-65bb8a08c8af

        :steps:
            1. Create a virt-who config (VHCONFIG1) for VMware
            2. Create a virt-who config (VHCONFIG2) for RHV
            3. Deploy VHCONFIG1 and VHCONFIG2 to the same virt-who server
            4. Create guests on the VMware and RHV hypervisors

        :expectedresults:
            1. Verify the correct information is reported to the Satellite.

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_multiple_config_multi_instance(self):
        """Create multiple configs for multiple virt-who instances

        :id: 053473df-7a83-4727-a96b-385fa87db1c9

        :steps:
            1. Create a virt-who config (VHCONFIG1) for VMware
            2. Create a virt-who config (VHCONFIG2) for RHV
            3. Deploy VHCONFIG1 and VHCONFIG2 to the 2 different
               virt-who servers
            4. Create guests on the VMware and RHV hypervisors

        :expectedresults:
            1. Verify the correct information is reported to the Satellite.

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_delete_config_delete_user(self):
        """Verify when a config is deleted the associated user is deleted.

        :id: 9fdee7f2-833c-47e0-9d58-cd0c9fdd15fe

        :steps:
            1. Create a virt-who configuration and deploy it to a
               virt-who server.
            2. Delete the configuration on the Satellite.

        :expectedresults:
            1. Verify the virt-who server can no longer send reports to the
               Satellite.

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_register_user_password(self):
        """Register guest with username/password

        :id: 84577e65-f5d4-40f0-80bf-919e9f71b4b4

        :steps:
            1. Create a virt-who configuration for a hypervisor
            2. Create a guest on a hypervisor.
            3. Attempt to register the guest using the admin
               username/password .
            4. Create a user with a content host registration role (REGUSER)

        :expectedresults:
            1. Verify a guest can be registered using the REGUSER user.

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_register_guess_no_subs(self):
        """Register guest with activation key with no subscriptions

        :id: 4a16d5b1-2c89-41d9-8ed3-55d8de2431ab

        :steps:
            1. Create a virt-who configuration for a hypervisor
            2. Create a activation key with no subscription configuration
            3. Create a guest on a hypervisor

        :expectedresults:
            1. Verify the guest can be registered using the activation key.

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_virt_who_proxy(self):
        """ Test virt-who with web proxy

        :id: 19007b6d-4845-48e6-aedf-2c4f76eebf91

        :steps:
            1. Create a virt-who configuration with a web proxy set
            2. Setup a Satellite and virt-who server such that the virt-who
               server can only reach the satellite via the web proxy.
            3. Deploy the configuration to the virt-who server.

        :expectedresults:
            1. Verify that reports are sent to the virt-who server via the
               proxy
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_virt_who_ignoreproxy(self):
        """ Proxy configured with ignore proxy variable

        :id: cf5b3039-2910-4cc6-adf1-f103ed3c478a

        :steps:
            1. Create a virt-who configuration with a web proxy, also
               set the ignore proxy to a list of hostnames, one of which
               is the satellite
            2. Deploy the configuration to the virt-who server.

        :expectedresults:
            1. Verify that reports are sent to the satellite and the proxy is
               not used.

        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_filtering_whitelist(self):
        """ Whitelist filters

        :id: f871ab49-1807-4a28-9bfc-a7f313602cc0

        :setup:
            Create a virt-who configuration with a pointing to a virtualization
            provider with 3 hypervisor hosts using UUID ids.

        :steps:
            1. Create a config with a whitelist that specifies 2 hypervisors.
            2. Deploy the config
            3. Repeat for each hypervisor id type (Hostname, Hwuuid)

        :expectedresults:
            Correct config file generated, non-whitelisted hypervisors are not
            reported.
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_filtering_blacklist(self):
        """ Blacklist filters

        :id: 9e823d10-1b67-45ea-b13d-75dd058de3d6

        :setup:
            Create a virt-who configuration with a virtualization provider with
            3 hypervisor hosts.

        :steps:
            1. Create a config with a blacklist that specifies 2 hypervisor
               hosts using UUID hypervisor ids.
            2. Deploy the config
            3. Repeat with each Hypervisor ID types (Hostname, hwuuid)

        :expectedresults:
            Correct config file generated, Blacklisted Hypervisors are not
            reported.
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_filtering_unlimited(self):
        """Unlimited filters

        :id: 979586c4-031e-4411-bb8b-eb17cad44651

        :steps:
            1. Create a configuration with unlimited filtering pointing to a
               virtualization provider with 3 hypervisor hosts

        :expectedresults:
            2. Verify all hypervisors hosts are reported to Satellite and
               attach to VDC subscriptions.
        """

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_rhel6(self):
        """
        :id: f0453a2d-fa81-40ae-81a9-330b529a3062

        :steps:
            1. Install VirtWho on a RHEL6 server

        :expectedresults:
            1. Verify a virt-who configuration script can be deployed on
               RHEL6 Server

        """
