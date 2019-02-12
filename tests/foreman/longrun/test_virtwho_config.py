"""Test for virt-who configure API

:Requirement: Virtwho-configure

:CaseLevel: Acceptance

:CaseComponent: API

:TestType: Functional

:CaseImportance: High

:CaseAutomation: notautomated

:Upstream: No
"""

from robottelo.decorators import run_only_on, stubbed, tier3
from robottelo.test import TestCase


class VirtWhoConfigLongRunTestCase(TestCase):

    @run_only_on('sat')
    @stubbed()
    @tier3
    def test_positive_hypervisors(self):
        """End to End scenarios. For all supported Hypervisors
           (Libvirt, vmware, RHEV, Hyper-V, Xen)

        :id: e3199512-f622-4ba6-9293-7557f378376f

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
