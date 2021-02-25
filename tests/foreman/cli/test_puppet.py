"""End to end test for Puppet funcionality

:Requirement: Puppet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""
import pytest

from robottelo.decorators import skip_if_not_set


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.on_premises_provisioning
@pytest.mark.upgrade
@skip_if_not_set('clients')
def test_positive_puppet_scenario():
    """Tests extensive all-in-one puppet scenario

    :id: d4fdba9f-6333-4d47-987b-ce920da20d77

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

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """


@pytest.mark.stubbed
@pytest.mark.tier3
@pytest.mark.on_premises_provisioning
@pytest.mark.upgrade
@skip_if_not_set('clients')
def test_positive_puppet_capsule_scenario():
    """Tests extensive all-in-one puppet scenario via Capsule

    :id: 51ffe74e-7131-43d0-a919-1175233b4763

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

    :CaseAutomation: NotAutomated

    :CaseLevel: System
    """
