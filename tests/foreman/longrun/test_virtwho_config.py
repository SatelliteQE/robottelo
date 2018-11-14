from robottelo.decorators import run_only_on, stubbed, tier1, tier3, tier4
from robottelo.test import TestCase



class VirtWhoConfigLongRunTestCase(TestCase):


    @tier3
    def test_virtwho_debug(self):
        pass



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

