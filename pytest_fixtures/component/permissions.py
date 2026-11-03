import pytest

from robottelo.constants import PERMISSIONS
from robottelo.enums import InstallMethod
from robottelo.utils.issue_handlers import is_open


def _remove_permissions(permissions, resource_type, permission_names):
    """Remove optional permissions if they are present in the expected list."""
    if resource_type in permissions:
        permissions[resource_type] = [
            permission
            for permission in permissions[resource_type]
            if permission not in permission_names
        ]


@pytest.fixture(scope="session")
def expected_permissions(session_target_sat):
    """Return the list of permissions valid for current instance."""

    permissions = {
        resource_type: resource_permissions.copy()
        for resource_type, resource_permissions in PERMISSIONS.items()
    }
    rpm_command = (
        'podman exec foreman rpm -qa'
        if session_target_sat.install_method == InstallMethod.FOREMANCTL
        else 'rpm -qa'
    )
    rpm_packages = session_target_sat.execute(rpm_command).stdout
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
        permissions.pop('ForemanOpenscap::ArfReport')
        permissions.pop('ForemanOpenscap::Policy')
        permissions.pop('ForemanOpenscap::ScapContent')
        permissions.pop('ForemanOpenscap::TailoringFile')
        permissions['SmartProxy'].remove('view_openscap_proxies')
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
    if 'rubygem-foreman_resource_quota' not in rpm_packages:
        permissions.pop('ForemanResourceQuota::ResourceQuota')
    if 'rubygem-foreman_scc_manager' not in rpm_packages:
        permissions.pop('SccAccount')
        permissions.pop('SccProduct')
    if 'rubygem-foreman_snapshot_management' not in rpm_packages:
        permissions['Host'].remove('view_snapshots')
        permissions['Host'].remove('create_snapshots')
        permissions['Host'].remove('destroy_snapshots')
        permissions['Host'].remove('revert_snapshots')
        permissions['Host'].remove('edit_snapshots')
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
        permissions.pop('Report')
    if 'rubygem-foreman_statistics' not in rpm_packages:
        permissions.pop('ForemanStatistics::Trend')
        permissions[None].remove('view_statistics')
    if 'rubygem-foreman_ansible_director' not in rpm_packages:
        permissions.pop('ForemanAnsibleDirector::AnsibleContentAssignment')
        permissions.pop('ForemanAnsibleDirector::ContentUnit')
        permissions.pop('ForemanAnsibleDirector::ExecutionEnvironment')
        permissions.pop('ForemanAnsibleDirector::LifecycleEnvironment')
        permissions.pop('ForemanAnsibleDirector::LifecycleEnvironmentPath')
        permissions['LookupValue'].remove('destroy_ansible_variable_overrides')
        permissions['LookupValue'].remove('edit_ansible_variable_overrides')
        permissions['LookupValue'].remove('create_ansible_variable_overrides')
        permissions['LookupValue'].remove('view_ansible_variable_overrides')
    if 'rubygem-foreman_monitoring' not in rpm_packages:
        permissions[None].remove('upload_monitoring_results')
        permissions['Host'].remove('view_monitoring_results')
        permissions['Host'].remove('manage_downtime_hosts')
    if 'foreman_templates' not in rpm_packages:
        permissions.pop('Template', None)

    # These plugin APIs are not supported on containerized (foremanctl) installs yet.
    # Match the gates used by the API endpoint coverage so exclusions disappear when
    # the corresponding product issues are closed.
    if is_open('SAT-40240'):
        permissions.pop('DiscoveryRule', None)
        _remove_permissions(
            permissions,
            'Host',
            {
                'auto_provision_discovered_hosts',
                'destroy_discovered_hosts',
                'edit_discovered_hosts',
                'provision_discovered_hosts',
                'submit_discovered_hosts',
                'view_discovered_hosts',
            },
        )
    if is_open('SAT-40441'):
        for resource_type in (
            'ForemanOpenscap::ArfReport',
            'ForemanOpenscap::Policy',
            'ForemanOpenscap::ScapContent',
            'ForemanOpenscap::TailoringFile',
        ):
            permissions.pop(resource_type, None)
        _remove_permissions(
            permissions,
            None,
            {'create_arf_reports', 'destroy_arf_reports', 'view_arf_reports'},
        )
        _remove_permissions(permissions, 'SmartProxy', {'view_openscap_proxies'})
    if is_open('SAT-44794'):
        permissions.pop('ForemanVirtWhoConfigure::Config', None)

    return permissions
