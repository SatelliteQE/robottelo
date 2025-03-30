import pytest

from robottelo.constants import PERMISSIONS


@pytest.fixture(scope="session")
def expected_permissions(session_target_sat):
    """Return the list of permissions valid for current instance."""

    permissions = PERMISSIONS.copy()
    rpm_packages = session_target_sat.execute('rpm -qa').stdout
    if 'rubygem-foreman_rh_cloud' not in rpm_packages:
        permissions.pop('InsightsHit')
        permissions[None].remove('generate_foreman_rh_cloud')
        permissions[None].remove('view_foreman_rh_cloud')
        permissions[None].remove('dispatch_cloud_requests')
        permissions[None].remove('control_organization_insights')
    if 'rubygem-foreman_bootdisk' not in rpm_packages:
        permissions[None].remove('download_bootdisk')
    if 'rubygem-foreman_virt_who_configure' not in rpm_packages:
        permissions.pop('ForemanVirtWhoConfigure::Config')
    if 'rubygem-foreman_openscap' not in rpm_packages:
        permissions.pop('ForemanOpenscap::Policy')
        permissions.pop('ForemanOpenscap::ScapContent')
        permissions[None].remove('destroy_arf_reports')
        permissions[None].remove('view_arf_reports')
        permissions[None].remove('create_arf_reports')
    if 'rubygem-foreman_remote_execution' not in rpm_packages:
        permissions.pop('JobInvocation')
        permissions.pop('JobTemplate')
        permissions.pop('RemoteExecutionFeature')
        permissions.pop('TemplateInvocation')
    if 'rubygem-foreman_puppet' not in rpm_packages:
        permissions.pop('ForemanPuppet::ConfigGroup')
        permissions.pop('ForemanPuppet::Environment')
        permissions.pop('ForemanPuppet::HostClass')
        permissions.pop('ForemanPuppet::Puppetclass')
        permissions.pop('ForemanPuppet::PuppetclassLookupKey')

    return permissions
