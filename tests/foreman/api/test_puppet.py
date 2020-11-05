"""End to end test for Puppet funcionality

:Requirement: Puppet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.config import settings
from robottelo.decorators import skip_if_not_set
from robottelo.test import APITestCase


@pytest.mark.run_in_one_thread
class PuppetTestCase(APITestCase):
    """Implements Puppet test scenario"""

    @classmethod
    @skip_if_not_set('clients')
    def setUpClass(cls):
        super().setUpClass()
        cls.sat6_hostname = settings.server.hostname

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_puppet_scenario(self):
        """Tests extensive all-in-one puppet scenario

        :id: 29635f43-e701-4539-844c-275545cdf9c4

        :Steps:

            1. Create an organization and upload a cloned manifest for it.
            2. Enable respective Satellite Tools repos and sync them.
            3. Create a product and a LFE
            4. Create a puppet repos within the product
            5. Upload motd puppet module into the repo
            6. Upload parameterizable puppet module and create smart params for
               it
            7. Create a CV and add Tools repo and puppet module(s)
            8. Publish and promote CV to the LFE
            9. Create AK with the product and enable Satellite Tools in it
            10. Create a libvirt compute resource
            11. Create a sane subnet and sane domain to be used by libvirt
            12. Create a hostgroup associated with all created entities
                (especially Puppet Classes has added puppet modules)
            13. Provision a host using the hostgroup on libvirt resource
            14. Assert that puppet agent can run on the host
            15. Assert that the puppet modules get installed by provisioning
            16. Run facter on host and assert that was successful

        :expectedresults: multiple asserts along the code

        :CaseAutomation: notautomated

        :CaseLevel: System
        """


@pytest.mark.run_in_one_thread
class PuppetCapsuleTestCase(APITestCase):
    """Implements Puppet test scenario with standalone capsule"""

    @classmethod
    @skip_if_not_set('clients')
    def setUpClass(cls):
        super().setUpClass()
        cls.sat6_hostname = settings.server.hostname

    @pytest.mark.stubbed
    @pytest.mark.tier3
    def test_positive_puppet_capsule_scenario(self):
        """Tests extensive all-in-one puppet scenario via Capsule

        :id: faffb182-93dc-4406-805c-3b2f10891854

        :Steps:
            1. Create an organization and upload a cloned manifest for it.
            2. Enable respective Satellite Tools repos and sync them.
            3. Create a product and a LFE
            4. Create a puppet repos within the product
            5. Upload motd puppet module into the repo
            6. Upload parameterizable puppet module and create smart params for
               it
            7. Create a CV and add Tools repo and puppet module(s)
            8. Publish and promote CV to the LFE
            9. Create AK with the product and enable Satellite Tools in it
            10. Create a libvirt compute resource
            11. Create a sane subnet and sane domain to be used by libvirt
            12. Create a hostgroup associated with all created entities
                (especially Puppet Classes has added puppet modules)
            13. Provision a host using the hostgroup on libvirt resource
            14. Assert that puppet agent can run on the host
            15. Assert that the puppet modules get installed by provisioning
            16. Run facter on host and assert that was successful

        :expectedresults: multiple asserts along the code

        :CaseAutomation: notautomated

        :CaseLevel: System
        """
