"""Test for Upgrade using leapp

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Leappintegration

:Assignee: shwsingh

:TestType: Functional

:CaseImportance: High

:Upstream: No

:Requirement: Product
"""
import pytest

from robottelo import manifests
from robottelo.config import settings


pytest.mark.parametrize('rhel_version', ["8.4", "8.6"])


def test_positive_rhel7_rhel8_upgrade(
    target_sat, rhel7_contenthost, module_org, module_lce, rhel_version
):
    """Test upgrade from RHEL7.9 to RHEL8 using LEAPP utility

    :id: 2395e00e-3fe0-4899-ac9a-816f709f5190

    :steps:
        1. Import Manifest and create Activation key
        2. Register the host to the Default Organization View using an activation key
        3. Enable RHEL7 and RHEL8 repos for upgrade
        4. Run leapp pre-upgrade and leapp upgrade

    :expectedresults:
        1. Verify host upgraded successfully to RHEL8
    """
    manifests.upload_manifest_locked(module_org.id)
    ak = target_sat.api.ActivationKey(
        content_view=module_org.default_content_view,
        max_hosts=100,
        organization=module_org,
        environment=target_sat.api.LifecycleEnvironment(id=module_org.library.id),
        auto_attach=True,
    ).create()
    # registering the content host with no content enabled/synced in the org
    # should create a client SCA cert with no content
    rhel7_contenthost.install_katello_ca(target_sat)
    rhel7_contenthost.register_contenthost(org=module_org.label, activation_key=ak.name)
    assert rhel7_contenthost.subscribed
    result = rhel7_contenthost.run('subscription-manager list --installed')
    assert "Subscribed" in result.stdout
    rhel7_contenthost.create_custom_repos(
        rhel7=settings.repos.rhel7_os,
        extras=settings.repos.rhel7_extras,
        baseos=settings.repos.rhel8_os.baseos,
        appstream=settings.repos.rhel8_os.appstream,
    )
    rhel7_contenthost.run("subscription-manager release --unset")
    rhel7_contenthost.run("yum update")
    rhel7_contenthost.run("yum install leapp-upgrade")
    rhel7_contenthost.run(f"leapp preupgrade --target {rhel_version}")
    rhel7_contenthost.run(f'leapp upgrade --target {rhel_version}')
    rhel_version = rhel7_contenthost.run("cat /etc/redhat-release")
    assert f"Red Hat Enterprise Linux Server release {rhel_version}" in rhel_version
