"""Tests for registration.

:Requirement: Registration

:CaseLevel: Acceptance

:CaseComponent: Registration

:Assignee: swadeley

:TestType: Functional

:Upstream: No
"""
import pytest

from robottelo.config import settings


@pytest.mark.tier1
def test_upgrade_katello_ca_consumer_rpm(
    module_org, module_location, target_sat, rhel7_contenthost
):
    """After updating the consumer cert the rhsm.conf file still points to Satellite host name
    and not Red Hat CDN for subscription.

    :id: c8d861ec-0d81-4d89-a8e1-02afecfd8171

    :steps:

        1. Get consumer crt source file
        2. Install rpm-build
        3. Use rpmbuild to change the version in the spec file
        4. Build new RPM with higher version number
        5. Install new RPM and assert no change in server URL

    :expectedresults: Server URL is still Satellite host name not Red Hat CDN

    :CaseAutomation: Automated

    :CaseImportance: High

    :customerscenario: true

    :BZ: 1791503
    """
    consumer_cert_name = f'katello-ca-consumer-{target_sat.hostname}'
    consumer_cert_src = f'{consumer_cert_name}-1.0-1.src.rpm'
    new_consumer_cert_rpm = f'{consumer_cert_name}-1.0-2.noarch.rpm'
    spec_file = f'{consumer_cert_name}.spec'
    vm = rhel7_contenthost
    # Install consumer cert and check server URL in /etc/rhsm/rhsm.conf
    assert vm.execute(
        f'rpm -Uvh "http://{target_sat.hostname}/pub/{consumer_cert_name}-1.0-1.noarch.rpm"'
    )
    # Check server URL is not Red Hat CDN's "subscription.rhsm.redhat.com"
    result = vm.execute('grep ^hostname /etc/rhsm/rhsm.conf')
    assert 'subscription.rhsm.redhat.com' not in result.stdout
    assert target_sat.hostname in result.stdout
    # Get consumer cert source file
    assert vm.execute(f'curl -O "http://{target_sat.hostname}/pub/{consumer_cert_src}"')
    # Install repo for build tools
    vm.create_custom_repos(rhel7=settings.repos.rhel7_os)
    result = vm.execute('[ -s "/etc/yum.repos.d/rhel7.repo" ]')
    assert result.status == 0
    # Install tools
    assert vm.execute('yum -y install rpm-build')
    # Install src to create the SPEC
    assert vm.execute(f'rpm -i {consumer_cert_src}')
    # rpmbuild spec file
    assert vm.execute(
        f'rpmbuild --define "name {consumer_cert_name}" --define "release 2" \
        -ba rpmbuild/SPECS/{spec_file}'
    )
    # Install new rpmbuild/RPMS/noarch/katello-ca-consumer-*-2.noarch.rpm
    assert vm.execute(f'yum install -y rpmbuild/RPMS/noarch/{new_consumer_cert_rpm}')
    # Check server URL is not Red Hat CDN's "subscription.rhsm.redhat.com"
    result = vm.execute('grep ^hostname /etc/rhsm/rhsm.conf')
    assert 'subscription.rhsm.redhat.com' not in result.stdout
    assert target_sat.hostname in result.stdout
    # Register as final check
    vm.register_contenthost(module_org.label)
    result = vm.execute('subscription-manager identity')
    # Result will be 0 if registered
    assert result.status == 0
