"""Test for virt-who configure API

:Requirement: Virtwho-configure

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import run_only_on, stubbed, tier1, tier2, tier3
from robottelo.test import TestCase, APITestCase


class VirtWhoConfigAPI(APITestCase):

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_vm_create(self):
        """ Register a vm on virt-who hyper visor
        :id: 701b22b8-fe92-4dd3-8d7d-c7b5efb7281b

        :steps:
            1. Create new VM in a supported hypervisor and check if it is reported to Satellite (waiting until the next virt-who report comes in)


        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_vm_create(self):
        """ Register a vm on non-virt-who hyper visor

        :id: abecc851-2475-4455-9c12-63a73fcb09bb

        :steps:
            1. Check if there are no virt-who reports reported if there is no change in guest-host mapping in hypervisor

        :return:
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_config_update(self):
        """Update a config, verify it it changed and redploy it

        :id: 6b2cc2c3-959b-468b-9865-0f01decd2249

        :steps:
            1. Update a config, verify it it changed and redploy it
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_postive_config_intervals(self):
        """ Verify intervals Intervals

        :id: 7e1bb498-4e63-44e8-be97-83e07601f56d

        :steps:
            1. Create a virt-who configuration with a reporting interval of every 1 hour.
            2. Verify a Virt-who configuration is created that sets the interval to 1 hour
            3. Verify a report is sent every hour
            4. Repeat for each supported interval.
        """


class VirtWhoConfigRoleApiTests(APITestCase):


    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_role_manager(self):
        """virt-who Manager

        :id: 4164bdde-f532-480c-b41e-747e87cf7d05
        :steps:
            1. Create a user with ONLY the virt-who manager role.
            2. Verify the user can create virt-who configurations
            3. Verify the user can edit an existing virt-who configuration
            4. Verify the user can delete a virt-who configuration
            5. Verify the user can see virt-who reporting information through the dashboard
            6. Verify the user can do no other actions
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_role_manager(self):
        """

        :id: e93b415a-7442-4f27-9c52-15c72f3e1414
        :steps:
            1. Verify the user can do no other actions

        :return:
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_role_reporter(self):
        """ Verify virt-who Reporter role

        :id: 63462338-a6f5-48eb-8b04-433c53882817

        :steps:
            a. Create a user with ONLY the virt-who reporter role.
            b. Configure virt-who WITHOUT using the virt-who config plugin. Set the Satellite the created user.
            c. Create a vm to cause virt-who to send a report to satellite.
            d. Verify the virt-who server send a report to the satellite.
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_role_reporter(self):
        """Verify virt-who Reporter role
            :id: 7dee0965-9ec4-4d76-a6ae-f2eec1960bac

            :steps:
                e. Verify the user can do no other actions other then those in test_positive_role_reporter

        :return:
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_role_viewer(self):
        """ Verify virt-who viewer role

        :id: 43314ae3-6768-44b5-a6bb-ee64ae381cd0

        :steps:
            a. Create a user with ONLY the virt-who Viewer role.
            b. Verify the user can view virt-who configurations.
            c. Verify the user CANNOT delete or modify virt-who configurations
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_negative_role_viewer(self):
        """Verify virt-who viewer role

        :id: 6919a748-423e-4843-bafe-eb98b7159c90

        :steps:
            d. Verify the user can do no other actions other then those in test_positive_role_viewer

        :return:
        """
        pass


class VirtWhoConfigUpgrade(APITestCase):

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_satellite_upgrade(self):
        """ Satellite upgrade

        :id: 0e301c08-8bef-4bea-a690-d4b0760949e8

        :Steps:

        1. Start with a satellite version before the virt-who configurator plugin
        2. Configure a virt-who server with virtualization provider (VP1) to send reports to the satellite.
        3. Upgrade the satellite to a version with virt-who configurator plugin.
        4. Configure a new virtualization provider (VP2)  with a VDC subscription
        5. Using the virt-who plugin, create a configuration for the new hypervisor.
        6. Deploy the configuration to the virt-who server
        7. Create a guest on VP1
        8. Create a guest on VP2
        9. verify that that reports on VP1 and VP2 are correct.
        """


class VirtWhoConfigGeneralTestcase(TestCase):

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_hypervisors(self):
        """End to End scenarios. For all supported Hypervisors (Libvirt, vmware, RHEV, Hyper-V, Xen)

        :id: ce67645a-8435-4e2a-9fd5-c54f2a11c44b

        :steps:
                1. Associate a VDC subscription to the hypervisor host
                2. Create a Virt-who configuration for the hypervisor.
                3. Deploy the virt-who configuration
                4. Create VM1 on the hypervisor
                5. Create activation key with Content view, but DO NOT associate subscription.
                6. Register  VM using the activation key.
                7. Wait until the next report comes to the satellite
                8. Verify the VM is report to the Satellite, and the VDC subscription is applied to it.
                9. Repeat for each supported hypervisor (Libvirt, vmware, RHEV, Hyper-V, Xen)
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_multiple_config_single_instance(self):
        """ Create multiple configs, add to same virt-who instance

        :id: 5d553f0d-4dc8-4ce4-8fa4-65bb8a08c8af

        :steps:
            1. Create a virt-who config (VHCONFIG1) for VMware
            2. Create a virt-who config (VHCONFIG2) for RHV
            3. Deploy VHCONFIG1 and VHCONFIG2 to the same virt-who server
            4. Create guests on the VMware and RHV hypervisors
            5. Verify the correct information is reported to the Satellite.

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_multiple_config_same_instance(self):
        """Create multiple configs for multiple virt-who instances

        :id: 053473df-7a83-4727-a96b-385fa87db1c9

        :steps:
                1. Create a virt-who config (VHCONFIG1) for VMware
                2. Create a virt-who config (VHCONFIG2) for RHV
                3. Deploy VHCONFIG1 and VHCONFIG2 to the 2 different virt-who server
                4. Create guests on the VMware and RHV hypervisors
                5. Verify the correct information is reported to the Satellite.


        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_delete_config_delete_user(self):
        """Verify when a config is deleted the associated user is deleted.

        :id: 9fdee7f2-833c-47e0-9d58-cd0c9fdd15fe

        :steps:
                1. Create a virt-who configuration and deploy it to a virt-who server.
                2. Delete the configuration on the Satellite.
                3. Verify the virt-who server can no longer send reports to the Satellite.

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_register_user_password(self):
        """Register guest with username/password

        :id: 84577e65-f5d4-40f0-80bf-919e9f71b4b4

        :steps:
                1. Create a virt-who configuration for a hypervisor
                2. Create a guest on a hypervisor.
                3. Attempt to register the guest using the admin username/password .
                4. Create a user with a content host registration role (REGUSER)
                5. Verify a guest can be registered using the REGUSER user.

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_register_guess_no_subs(self):
        """Register guest with activation key with no subscriptions

        :id: 4a16d5b1-2c89-41d9-8ed3-55d8de2431ab

        :steps:
                1. Create a virt-who configuration for a hypervisor
                2. Create a activation key with no subscription configuration
                3. Create a guest on a hypervisor
                4. Verify the guest can be registered using the activation key.

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_virt_who_proxy(self):
        """ Test virt-who with web proxy

        :id: 19007b6d-4845-48e6-aedf-2c4f76eebf91

        :steps:
                1. Create a virt-who configuration with a web proxy set
                2. Setup a Satellite and virt-who server such that the virt-who server can only reach the satellite via the web proxy.
                3. Deploy the configuration to the virt-who server.
                4. Verify that reports are sent to the virt-who server.
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_filtering_whitelist(self):
        """ Whitelist filters
        :id: f871ab49-1807-4a28-9bfc-a7f313602cc0

        :setup:
            Create a virt-who configuration with a pointing to a virtualization provider with 3 hypervisor hosts.

        :steps:
            a.  Create a whitelist that specifies 2 hypervisor hosts using UUID hypervisor ids.
            b. Create a guests on the 2 hypervisors that match the whitelist, verify they are reported and can attach to a VDC subscriptions.
            c. Create a guest on a hypervisor that does not match the whitelist, verify it CANNOT get a VDC subscription

        :expectedresult: Correct config file generated, non-whitelisted servers are not reported.
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_filtering_blacklist(self):
        """ Blacklist filters

        :id: 9e823d10-1b67-45ea-b13d-75dd058de3d6

        :setup:
            Create a virt-who configuration with a pointing to a virtualization provider with 3 hypervisor hosts.

        :steps:
                a. Create a blacklist that specifies 2 hypervisor hosts using UUID hypervisor ids.
                b. Create a whitelist with 2 hypervisor that match the blacklist, verify they are not reported and CANNOT attach to a VDC subscriptions.
                c. Create a guest on a hypervisor that does not match the blacklist, verify it can attach to a VDC subscription
                d. Repeat with each Hypervisor ID types (Hostname, hwuuid)

        :expectedresult: Correct config file generated, Blacklisted Hypervisors are not reported.
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_filtering_unlimited(self):
        """Unlimited filters

        :id: 979586c4-031e-4411-bb8b-eb17cad44651

        :steps:
                a. Create a configuration with unlimited filtering pointing to a virtualization provider with 3 hypervisor hosts
                b. Verify all hypervisors hosts are reported to Satellite and attach to VDC subscriptions.
        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_intervals(self):
        """ Verify Intervals
        :id: 76a31b43-1738-4e6a-acd7-604fff19ae79

        :steps:
                1. Create a virt-who configuration with a reporting interval of every 1 hour.
                2. Verify a Virt-who configuration is created that sets the interval to 1 hour
                3. Verify a report is sent every hour
                4. Repeat for each supported interval.

        :expectedresult: Config file is generaled with correct interval set.

        """

    @run_only_on('sat')
    @stubbed()
    @tier1
    def test_positive_rhel6(self):
        """
        :id: f0453a2d-fa81-40ae-81a9-330b529a3062

        :steps:
            1. Verify a virt-who configuration script can be deployed on RHEL6 Server

        """










