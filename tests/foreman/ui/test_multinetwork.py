# -*- encoding: utf-8 -*-
"""Test class for Multi-Network Support feature

:Requirement: Multinetwork

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: UI

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
from robottelo.decorators import stubbed, tier3, upgrade
from robottelo.test import UITestCase


class MultinetworkTestCase(UITestCase):
    """Implements Multi Network support tests in UI."""

    @stubbed()
    @tier3
    def test_positive_create_with_dhcp_ipam(self):
        """Create host with default interface and set 'DHCP' for IPAM
        and BootMode for provisioning subnet

        :id: e953dbf1-3592-48d6-b217-956676fd04d7

        :Setup: Provisioning should be configured

        :Steps:

            1. Set 'DHCP' for IPAM and BootMode for provisioning subnet
            2. All other fields on subnet page should be filled

        :expectedresults: Host should be provisioned with correct configuration
            under /etc/sysconfig/network-scripts/ifcfg-<interface>

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_create_with_non_specified_internal_db_ipam_dhcp(self):
        """Create host with default interface when IPAM set as
        'Internal DB' (without specifying start and end range) and BootMode
        set as 'DHCP' for provisioning subnet

        :id: 558a92e9-e769-4093-8a38-4a3e2f820aa2

        :Setup: Provisioning should be configured

        :Steps:

            1. Set IPAM with 'Internal DB' and BootMode with 'DHCP for
                provisioning subnet
            2. All other fields on subnet page should be filled except start
                and end IP range

        :expectedresults: Host should be provisioned with correct configuration
            under /etc/sysconfig/network-scripts/ifcfg-<interface>

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_create_with_specified_internal_db_ipam_dhcp(self):
        """Create host with default interface when IPAM set as
        'Internal DB' (with start and end IP range) and BootMode set as
        'DHCP' for provisioning subnet

        :id: c5d0eb65-33d6-4126-800c-ff3bf97e7fe0

        :Setup: Provisioning should be configured

        :Steps:

            1. Set IPAM with 'Internal DB' and BootMode with 'DHCP for
                provisioning subnet
            2. All other fields on subnet page should be filled including start
                and end IP range

        :expectedresults: Host should be provisioned with correct configuration
            under /etc/sysconfig/network-scripts/ifcfg-<interface>

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_create_with_specified_internal_db_ipam_static(self):
        """Create host with default interface when IPAM set as
        'Internal DB' (with start and end IP range) and BootMode set as
        'Static' for provisioning subnet

        :id: 9130917a-b0f5-4fb3-a516-733ee569218e

        :Setup: Provisioning should be configured

        :Steps:

            1. Set IPAM with 'Internal DB' and BootMode with 'Static' for
                provisioning subnet
            2. All other fields on subnet page should be filled including start
                and end IP range

        :expectedresults: Host should be provisioned with correct configuration
            under /etc/sysconfig/network-scripts/ifcfg-<interface>

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_create_with_non_specified_internal_db_ipam_static(self):
        """Create host with default interface when IPAM set as
        'Internal DB' (without start and end IP range) and BootMode set
        as 'Static' for provisioning subnet

        :id: 36602343-377d-419a-8ad5-e0b37ceaddba

        :Setup: Provisioning should be configured

        :Steps:

            1. Set IPAM with 'Internal DB' and BootMode with 'Static' for
                provisioning subnet
            2. All other fields on subnet page should be filled except start
                and end IP range

        :expectedresults: Host should be provisioned with correct configuration
            under /etc/sysconfig/network-scripts/ifcfg-<interface>

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_create_with_specified_dhcp_ipam_static(self):
        """Create host with default interface when IPAM set as 'DHCP'
        (with start and end IP range) and BootMode set as 'Static' for
        provisioning subnet

        :id: 37b950e8-ad30-4edd-aca8-54a7e16315bc

        :Setup: Provisioning should be configured

        :Steps:

            1. Set IPAM with 'DHCP' and BootMode with 'Static' for provisioning
                subnet
            2. All other fields on subnet page should be filled including start
                and end IP range

        :expectedresults: Host should be provisioned with correct configuration
            under /etc/sysconfig/network-scripts/ifcfg-<interface>

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_create_with_non_specified_dhcp_ipam_static(self):
        """Create host with default interface when IPAM set as 'DHCP'
        (without start and end IP range) and BootMode set as 'Static' for
        provisioning subnet

        :id: e1fe6337-8620-4b23-868a-ba2b95b4d046

        :Setup: Provisioning should be configured

        :Steps:

            1. Set IPAM with 'DHCP' and BootMode with 'Static' for provisioning
                subnet
            2. All other fields on subnet page should be filled except start
                and end IP range

        :expectedresults: Host should be provisioned with correct configuration
            under /etc/sysconfig/network-scripts/ifcfg-<interface>

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_create_none_ipam_static(self):
        """Create host with default interface when IPAM set as 'None'
        and BootMode set as 'Static' for provisioning subnet

        :id: 693725c9-5c46-4ea8-8f22-96e2a0808563

        :Setup: Provisioning should be configured

        :Steps:

            1. Set IPAM with 'None' and BootMode with 'Static' for provisioning
                subnet
            2. All other fields on subnet page should be filled

        :expectedresults: Host should be provisioned with correct configuration
            under /etc/sysconfig/network-scripts/ifcfg-<interface>

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_create_none_ipam_dhcp(self):
        """Create host with default interface when IPAM set as 'None'
        and BootMode set as 'DHCP' for provisioning subnet

        :id: 8feea115-ecf3-4f1d-a579-484188377a9d

        :Setup: Provisioning should be configured

        :Steps:

            1. Set IPAM with 'None' and BootMode with 'DHCP' for provisioning
                subnet
            2. All other fields on subnet page should be filled

        :expectedresults: Host should be provisioned with correct configuration
            under /etc/sysconfig/network-scripts/ifcfg-<interface>

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_add_alias_interface_with_mac(self):
        """Add an alias interface with mac different than
        primary interface's mac

        :id: 93671234-77af-494d-8d29-8d7255c94437

        :Setup: Provisioning should be configured

        :Steps:

            1. Go to 'Network' tab of 'New host' page
            2. Click on 'Add Interface' from 'Network tab
            3. Choose Type: 'Interface'
            4. mac address: should be different from primary interface
            5. Identifier: eth0:0
            6. Select 'Managed'
            7. Select 'Virtual Nic'
            8. attached_to: identifier of primary interface(eth0)
            9. Fill all other details correctly in new host form and submit it

        :expectedresults: Validation error should be raised as mac address of
            alias interface should be same as of primary interface

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_add_alias_interface_without_nic(self):
        """Add an alias interface without selecting virtual nic

        :id: bf840727-b9a0-400e-9167-f1cdbca99546

        :Setup: Provisioning should be configured

        :Steps:

            1. Go to 'Network' tab of 'New host' page
            2. Click on 'Add Interface' from 'Network tab
            3. Choose Type: 'Interface'
            4. mac address: mac should be same as of primary interface
            5. Identifier: eth0:0
            6. Select 'Managed'
            7. Fill all other details correctly in new host form and submit it

        :expectedresults: Validation error should be raised as two nics can not
            have same mac

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_add_alias_interface_without_attached_to(self):
        """Add an alias interface without defining
        'attached_to' interface under 'Virtual Nic'

        :id: 2f9273fb-a598-439c-af44-fec11548d918

        :Setup: Provisioning should be configured

        :Steps:

            1. Go to 'Network' tab of 'New host' page
            2. Click on 'Add Interface' from 'Network tab
            3. Choose Type: 'Interface'
            4. mac address: mac should be same as of primary interface
            5. Identifier: eth0:0
            6. Select 'Managed'
            7. Select 'Virtual Nic'
            8. Do not specify anything under 'attached_to'
            9. Fill all other details correctly in new host form and submit it

        :expectedresults: Validation error should be raised as attached_to is
            mandatory option to create alias interface

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_add_alias_interface_with_dhcp_bootmode(self):
        """Add an alias interface when bootMode set to 'DHCP'
        mode under selected subnet

        :id: 9f2a916c-f8df-4d8b-b597-916f27d89073

        :Setup: Provisioning should be configured

        :Steps:

            1. Go to 'Network' tab of 'New host' page
            2. Click on 'Add Interface' from 'Network tab
            3. Choose Type: 'Interface'
            4. mac address: mac should be same as of primary interface
            5. Identifier: eth0:0
            6. Select 'Managed'
            7. Select 'Virtual Nic'
            8. attached_to: identifier of primary interface(eth0)
            9. Go to Infrastructure -> Subnet
            10. Set IPAM mode to 'Internal DB'
            11. BootMode 'DHCP'
            12. Fill all other details correctly in new host form and submit it

        :expectedresults: Validation error should be raised as you can't
            configure alias interface in 'DHCP' mode.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_add_alias_with_static_bootmode(self):
        """Add an alias interface when bootMode set to 'Static'
        mode under selected subnet

        :id: dc8a9056-bc1c-43b6-80b8-f9a105264755

        :Setup: Provisioning should be configured

        :Steps:

            1. Go to 'Network' tab of 'New host' page
            2. Click on 'Add Interface' from 'Network tab
            3. Choose Type: 'Interface'
            4. mac address: mac should be same as of primary interface
            5. Identifier: eth0:0
            6. Select 'Managed'
            7. Select 'Virtual Nic'
            8. attached_to: identifier of primary interface(eth0)
            9. Go to Infrastructure → Subnet
            10. Set IPAM mode to 'Internal DB'
            11. BootMode 'Static'
            12. Fill all other details correctly in new host form and submit it

        :expectedresults: Interface should be configured successfully and
            correct configuration should displayed on proviisoned host under
            /etc/sysconfig/network-scripts/ifcfg-<interface_name>

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_add_alias_interface_same(self):
        """Add an interface with same identifier of exiting interface

        :id: b976fe33-6b08-4f64-ba46-d32601e6f71f

        :Setup: Provisioning should be configured

        :Steps:

            1. Go to 'Network' tab of 'New host' page
            2. Click on 'Add Interface' from 'Network tab
            3. Choose Type: 'Interface'
            4. mac address: mac should be same as of primary interface
            5. Identifier: eth0:0
            6. Select 'Managed'
            7. Select 'Virtual Nic'
            8. attached_to: identifier of primary interface(eth0)
            9. Go to Infrastructure → Subnet
            10. Set IPAM mode to 'Internal DB'
            11. BootMode 'Static'
            12. Fill all other details correctly in new host form and submit it

        :expectedresults: Validation error should be raised on UI

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_delete_alias_interface(self):
        """Delete an alias interface

        :id: 8370940a-088a-403b-9b77-1be499c992e7

        :Setup: Provisioning should be configured

        :Steps:

            1. Create an aliased interface
            2. Edit the new host → Network → delete the selected interface
            3. submit form

        :expectedresults: Interface should be deleted successfully

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_add_bond_interface_using_two_existing(self):
        """Add bond interface using existing two interfaces

        :id: 6d72a89a-48c4-44a9-afb4-d1427264695d

        :Setup: Provisioning should be configured

        :Steps:

            1. Go to 'Network' tab of 'New host' page
            2. Click on 'Add Interface' from 'Network tab
            3. Choose Type: 'Bond'
            4. mac address: mac should be same as of any of two primary
               interfaces 5. Identifier: bond0
            5. Select 'Managed'
            6. Mode 'Balanced rr'
            7. attached_devices: eth0, eth1
            8. Go to Infrastructure → Subnet
            9. Set IPAM mode to 'Internal DB'
            10. BootMode 'Static'
            11. Fill all other details correctly in new host form and submit it

        :expectedresults: Interface should be configured successfully with name
            bond0

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_negative_add_bond_interface_without_mac(self):
        """Add bond interface using existing two interfaces without
        specifying mac

        :id: 51498c07-a3ba-40d5-a521-bad3d012ce0e

        :Setup: Provisioning should be configured

        :Steps:

            1. Go to 'Network' tab of 'New host' page
            2. Click on 'Add Interface' from 'Network tab
            3. Choose Type: 'Bond'
            4. mac address: leave it blank
            5. Identifier: bond0
            6. Select 'Managed'
            7. Mode 'Balanced rr'
            8. attached_devices: eth0, eth1
            9. Go to Infrastructure → Subnet
            10. Set IPAM mode to 'Internal DB'
            11. BootMode 'Static'
            12. Fill all other details correctly in new host form and submit it

        :expectedresults: UI should raise validation error as user shouldn't be
            allowed create bond interface without mac

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_add_bond_interface_without_attached_device(self):
        """Add bond interface without specifying attached devices

        :id: 1ed737f5-a371-4bcb-95b5-fa75e372654b

        :Setup: Provisioning should be configured

        :Steps:

            1. Go to 'Network' tab of 'New host' page
            2. Click on 'Add Interface' from 'Network tab
            3. Choose Type: 'Bond'
            4. mac address: leave it blank
            5. Identifier: bond0
            6. Select 'Managed'
            7. Mode 'Balanced rr'
            8. attached_devices: leave it blank
            9. Go to Infrastructure → Subnet
            10. Set IPAM mode to 'Internal DB'
            11. BootMode 'Static'
            12. Fill all other details correctly in new host form and submit it

        :expectedresults: Interface should be configured successfully without
            attaching any device to it.

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_add_bond_interface(self):
        """Add bond interface with one alias interface

        :id: 0252b5a7-3854-47d9-9791-863ad245308d

        :Setup: Provisioning should be configured

        :Steps:

            1. Alias interface should already be configured
            2. Go to 'Network' tab of 'New host' page
            3. Click on 'Add Interface' from 'Network tab
            4. Choose Type: 'Bond'
            5. mac address: leave it blank
            6. Identifier: bond0
            7. Select 'Managed'
            8. Mode 'Balanced rr'
            9. attached_devices: eth0, eth0:0
            10. Go to Infrastructure → Subnet
            11. Set IPAM mode to 'Internal DB'
            12. BootMode 'Static'
            13. Fill all other details correctly in new host form and submit it

        :expectedresults: Interface should be configured successfully with name
            bond0 attached to eth0 eth0:0

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    @upgrade
    def test_positive_add_bmc_interface(self):
        """Add bmc interface

        :id: 7c5a9bb8-70c9-4fe3-a61e-179d7946bb62

        :Setup: Provisioning should be configured

        :Steps:

            1. Go to 'Network' tab of 'New host' page
            2. Click on 'Add Interface' from 'Network tab
            3. Choose Type: 'BMC'
            4. mac address: Mac of BMC
            5. Identifier: bmc
            6. Select 'Managed'
            7. User name:
            8. password:
            9. Provider: IPMI
            10. Fill all other details correctly in new host form and submit it

        :expectedresults: Interface should be configured successfully and user
            should get On/OFF button on host page

        :CaseAutomation: notautomated

        :CaseLevel: System
        """

    @stubbed()
    @tier3
    def test_positive_add_bmc_interface_without_mac(self):
        """Add bmc interface without mac

        :id: 3daf53ed-2ef1-4503-b181-6f96377b187e

        :Setup: Provisioning should be configured

        :Steps:

            1. Go to 'Network' tab of 'New host' page
            2. Click on 'Add Interface' from 'Network tab
            3. Choose Type: 'BMC'
            4. mac address: blank
            5. Identifier: bmc
            6. Select 'Managed'
            7. User name:
            8. password:
            9. Provider: IPMI
            10. Fill all other details correctly in new host form and submit it

        :expectedresults: UI should raise validation error

        :CaseAutomation: notautomated

        :CaseLevel: System
        """
