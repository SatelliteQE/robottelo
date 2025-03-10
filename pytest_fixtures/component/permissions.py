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
    if 'gem-foreman_virt_who_configure' not in rpm_packages:
        permissions.pop('ForemanVirtWhoConfigure::Config')
    if 'gem-foreman_openscap' not in rpm_packages:
        permissions.pop('ForemanOpenscap::Policy')
        permissions.pop('ForemanOpenscap::ScapContent')
        permissions[None].remove('destroy_arf_reports')
        permissions[None].remove('view_arf_reports')
        permissions[None].remove('create_arf_reports')
    if 'gem-foreman_remote_execution' not in rpm_packages:
        permissions.pop('JobInvocation')
        permissions.pop('JobTemplate')
        permissions.pop('RemoteExecutionFeature')
        permissions.pop('TemplateInvocation')
    if 'gem-foreman_puppet' not in rpm_packages:
        permissions.pop('ForemanPuppet::ConfigGroup')
        permissions.pop('ForemanPuppet::Environment')
        permissions.pop('ForemanPuppet::HostClass')
        permissions.pop('ForemanPuppet::Puppetclass')
        permissions.pop('ForemanPuppet::PuppetclassLookupKey')
    if 'rubygem-foreman_scc_manager' not in rpm_packages:
        permissions.pop('SccAccount')
        permissions.pop('SccProduct')
    if 'rubygem-foreman_snapshot_management' not in rpm_packages:
        permissions['Host'].remove('view_snapshots')
        permissions['Host'].remove('create_snapshots')
        permissions[None].remove('destroy_snapshots')
        permissions[None].remove('revert_snapshots')
        permissions[None].remove('edit_snapshots')
    if 'gem-foreman_salt' not in rpm_packages:
        permissions['Host'].remove('saltrun_hosts')
        permissions['SmartProxy'].remove('destroy_smart_proxies_salt_autosign')
        permissions['SmartProxy'].remove('view_smart_proxies_salt_autosign')
        permissions['SmartProxy'].remove('destroy_smart_proxies_salt_keys')
        permissions['SmartProxy'].remove('view_smart_proxies_salt_keys')
        permissions['SmartProxy'].remove('edit_smart_proxies_salt_keys')
        permissions['SmartProxy'].remove('auth_smart_proxies_salt_autosign')
        permissions['SmartProxy'].remove('create_smart_proxies_salt_autosign')
        permissions.pop('ForemanSalt::SaltVariable')
        permissions.pop('ForemanSalt::SaltEnvironment')
        permissions.pop('ForemanSalt::SaltModule')

    return permissions
