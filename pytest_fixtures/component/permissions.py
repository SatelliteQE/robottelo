import pytest

from robottelo.constants import PERMISSIONS


@pytest.fixture(scope="session")
def expected_permissions(session_target_sat):
    """Return the list of permissions valid for current instance."""

    permissions = PERMISSIONS.copy()
    if session_target_sat.is_upstream:
        permissions[None].extend(permissions.pop('DiscoveryRule'))
        permissions[None].remove('app_root')
        permissions[None].remove('attachments')
        permissions[None].remove('configuration')
        permissions[None].remove('logs')
        permissions[None].remove('view_cases')
        permissions[None].remove('view_log_viewer')

    result = session_target_sat.execute('rpm -qa | grep rubygem-foreman_openscap')
    if result.status != 0:
        permissions.pop('ForemanOpenscap::Policy')
        permissions.pop('ForemanOpenscap::ScapContent')
        permissions[None].remove('destroy_arf_reports')
        permissions[None].remove('view_arf_reports')
        permissions[None].remove('create_arf_reports')
    result = session_target_sat.execute('rpm -qa | grep rubygem-foreman_remote_execution')
    if result.status != 0:
        permissions.pop('JobInvocation')
        permissions.pop('JobTemplate')
        permissions.pop('RemoteExecutionFeature')
        permissions.pop('TemplateInvocation')

    return permissions
