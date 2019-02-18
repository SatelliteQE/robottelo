"""Provisioning tests

:Requirement: Provisioning

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: Provisioning

:TestType: Functional

:CaseImportance: High

:Upstream: No
"""

from robottelo.decorators import (
    stubbed,
    tier3,
)


@stubbed
@tier3
def test_rhel_pxe_provisioning_on_libvirt():
    """Provision RHEL system via PXE on libvirt and make sure it behaves

    :id: a272a594-f758-40ef-95ec-813245e44b63

    :steps:
        1. Provision RHEL system via PXE on libvirt
        2. Check that resulting host is registered to Satellite
        3. Check host can install package from Satellite

    :expectedresults:
        1. Host installs
        2. Host is registered to Satellite and subscription status is 'Success'
        3. Host can install package from Satellite

    CaseLevel: Integration
    """
