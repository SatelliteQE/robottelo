"""Test class for the capsule CLI.

:Requirement: Capsule

:CaseAutomation: Automated

:CaseLevel: Component

:CaseComponent: Capsule

:Assignee: vsedmik

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
from fauxfactory import gen_string

from robottelo.hosts import Capsule
from robottelo.utils.installer import InstallerCommand

pytestmark = [pytest.mark.destructive]


@pytest.mark.tier1
def test_positive_capsule_certs_generate_with_special_char(target_sat):
    """Verify capsule-certs-generate with special character in organization

    :id: e9dc6a64-4be4-11ed-8b27-9f5cc2f1b246

    :expectedresults: capsule-certs-generate works

    :CaseLevel: Component

    :BZ: 1908841

    :customerscenario: true
    """
    capsule = Capsule('capsule.example.com')
    # Create an org with a special char in its name and set it as the default using installer
    org = target_sat.api.Organization(name=f"{gen_string('alpha')}'s").create()
    result = target_sat.install(InstallerCommand(f'foreman-initial-organization "{org.name}"'))
    assert result.status == 0
    # Verify capsule-certs-generate works with special chars in org.name
    _, result, _ = target_sat.capsule_certs_generate(capsule)
    assert result.status == 0
    assert f'subscription-manager register --org "{org.name}"' in result.stdout
