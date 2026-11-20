from manifester import Manifester
import pytest
from wait_for import TimedOutError, wait_for

from robottelo.config import settings
from robottelo.constants import (
    CAPSULE_REGISTRATION_OPTS,
    DEFAULT_ARCHITECTURE,
    REPOS,
    VULNERABLE_PACKAGES,
)


def _activation_key_content_payload(module_target_sat_insights, organization):
    """Build ActivationKey content payload compatible with Nailgun schema."""
    content_view = organization.default_content_view
    environment = module_target_sat_insights.api.LifecycleEnvironment(id=organization.library.id)
    activation_key_fields = module_target_sat_insights.api.ActivationKey()._fields

    if {'content_view', 'environment'}.issubset(activation_key_fields):
        return {'content_view': content_view, 'environment': environment}

    if 'content_view_environment_ids' in activation_key_fields:
        cvenv_id = module_target_sat_insights.api_factory.get_cvenv_id(content_view, environment)
        return {'content_view_environment_ids': [cvenv_id]}

    raise RuntimeError(f'Unsupported ActivationKey schema fields: {list(activation_key_fields)}')


def enable_insights(host, satellite, org, activation_key):
    """Configure remote execution and insights-client on a host"""
    host.configure_rex(satellite=satellite, org=org, register=False)
    host.configure_insights_client(
        satellite=satellite,
        activation_key=activation_key,
        org=org,
        rhel_distro=f'rhel{host.os_version.major}',
    )
    is_iop = satellite.iop_enabled
    # Status may change the local marker; preserve IoP's pre-status fallback.
    local_registered = (
        is_iop
        and host.execute('test -f "${INSIGHTS_CONF_DIR:-/etc/insights-client}/.registered"').status
        == 0
    )
    result = host.check_insights_registration(satellite)
    is_registered = result.status == 0 or local_registered
    assert is_registered, f'insights-client not registered on {host.hostname}: {result.stdout}'
    # Sync inventory if using hosted Insights
    if not is_iop:
        satellite.generate_inventory_report(org)
        satellite.sync_inventory_status(org)


@pytest.fixture(scope='module')
def module_target_sat_insights(request, module_target_sat):
    """
    A module-level fixture to provide a Satellite configured for Insights.
    By default, it returns the existing Satellite provided by module_target_sat.

    If parametrized with a false value, then it will deploy and return a Satellite with
    iop-advisor-engine (local Insights advisor) configured.
    """
    hosted_insights = getattr(request, 'param', True)
    return module_target_sat if hosted_insights else request.getfixturevalue('module_satellite_iop')


@pytest.fixture(scope='module')
def module_els_manifest():
    """Module-scoped ELS manifest

    Uses a different manifest (els_rhel_manifest) than module_sca_manifest
    (golden_ticket) so we get a different allocation/export and avoid the Candlepin error
    'This subscription management application has already been imported by another owner'.
    """
    with Manifester(manifest_category=settings.manifest.els_rhel_manifest) as manifest:
        yield manifest


@pytest.fixture(scope='module')
def module_els_manifest_org(module_target_sat_insights, module_els_manifest):
    """A module level fixture to get organization with els manifest."""
    org = module_target_sat_insights.api.Organization().create()
    module_target_sat_insights.upload_manifest(org.id, module_els_manifest.content)
    return org


@pytest.fixture(scope='module')
def rhcloud_manifest_org(module_target_sat_insights, module_sca_manifest):
    """A module level fixture to get organization with manifest."""
    org = module_target_sat_insights.api.Organization().create()
    module_target_sat_insights.upload_manifest(org.id, module_sca_manifest.content)
    proxy = module_target_sat_insights.nailgun_smart_proxy.read()
    if org.id not in [proxy_org.id for proxy_org in proxy.organization]:
        proxy.organization = [*proxy.organization, org]
        proxy.update(['organization'])
    return org


@pytest.fixture(scope='module')
def rhcloud_activation_key(module_target_sat_insights, rhcloud_manifest_org):
    """A module-level fixture to create an Activation key in rhcloud_manifest_org"""
    return module_target_sat_insights.api.ActivationKey(
        **_activation_key_content_payload(module_target_sat_insights, rhcloud_manifest_org),
        organization=rhcloud_manifest_org,
        service_level='Self-Support',
        purpose_usage='test-usage',
        purpose_role='test-role',
    ).create()


@pytest.fixture(scope='module')
def activation_key_with_els_manifest_org(module_target_sat_insights, module_els_manifest_org):
    """A module-level fixture to create an Activation key in module_els_manifest_org"""
    return module_target_sat_insights.api.ActivationKey(
        **_activation_key_content_payload(module_target_sat_insights, module_els_manifest_org),
        organization=module_els_manifest_org,
    ).create()


@pytest.fixture(scope='module')
def rhcloud_registered_hosts(
    rhcloud_activation_key, rhcloud_manifest_org, mod_content_hosts, module_target_sat_insights
):
    """Fixture that registers content hosts to Satellite and Insights."""
    for vm in mod_content_hosts:
        vm.configure_insights_client(
            satellite=module_target_sat_insights,
            activation_key=rhcloud_activation_key,
            org=rhcloud_manifest_org,
            rhel_distro=f"rhel{vm.os_version.major}",
        )
        assert vm.subscribed
    return mod_content_hosts


@pytest.fixture
def rhel_insights_vm(
    module_target_sat_insights,
    rhcloud_activation_key,
    rhcloud_manifest_org,
    rhel_contenthost,
):
    """A function-level fixture to create rhel content host registered with insights."""
    enable_insights(
        rhel_contenthost, module_target_sat_insights, rhcloud_manifest_org, rhcloud_activation_key
    )
    return rhel_contenthost


@pytest.fixture
def rhel_insights_vms(
    module_target_sat_insights,
    rhcloud_activation_key,
    rhcloud_manifest_org,
    content_hosts,
):
    """A function-level fixture to create rhel content hosts registered with insights."""
    for content_host in content_hosts:
        enable_insights(
            content_host, module_target_sat_insights, rhcloud_manifest_org, rhcloud_activation_key
        )
    return content_hosts


@pytest.fixture
def inventory_settings(module_target_sat_insights):
    hostnames_setting = module_target_sat_insights.update_setting(
        'obfuscate_inventory_hostnames', False
    )
    ip_setting = module_target_sat_insights.update_setting('obfuscate_inventory_ips', False)
    packages_setting = module_target_sat_insights.update_setting(
        'exclude_installed_packages', False
    )
    parameter_tags_setting = module_target_sat_insights.update_setting(
        'include_parameter_tags', False
    )

    yield

    module_target_sat_insights.update_setting('obfuscate_inventory_hostnames', hostnames_setting)
    module_target_sat_insights.update_setting('obfuscate_inventory_ips', ip_setting)
    module_target_sat_insights.update_setting('exclude_installed_packages', packages_setting)
    module_target_sat_insights.update_setting('include_parameter_tags', parameter_tags_setting)


@pytest.fixture(scope='module')
def rhcloud_capsule(
    module_capsule_host, module_target_sat_insights, rhcloud_manifest_org, default_location
):
    """Configure the capsule instance with the satellite from settings.server.hostname"""
    org = rhcloud_manifest_org
    module_capsule_host.capsule_setup(
        sat_host=module_target_sat_insights, **CAPSULE_REGISTRATION_OPTS
    )
    module_target_sat_insights.cli.Capsule.update(
        {
            'name': module_capsule_host.hostname,
            'organization-ids': org.id,
            'location-ids': default_location.id,
        }
    )
    return module_capsule_host


def trigger_cve_sync(satellite, best_effort=False, assert_start=False):
    """Start CVE sync services and wait for each to complete.

    Args:
        satellite: Satellite instance used to run IoP sync services.
        best_effort: If True, ignore service wait timeouts.
        assert_start: If True, assert that each `systemctl start` succeeds.
    """
    for service in ('iop-cvemap-download', 'iop-service-vuln-vmaas-sync'):
        start_result = satellite.execute(f'systemctl start {service}')
        if assert_start:
            assert start_result.status == 0, f'Failed to start {service}: {start_result.stderr}'
        try:
            wait_for(
                lambda svc=service: satellite.execute(f'systemctl is-active {svc}').status != 0,
                timeout=300,
                delay=10,
                handle_exception=True,
            )
        except TimedOutError:
            if not best_effort:
                raise


def cleanup_stale_insights_state(client):
    """Clean up stale insights-client state, re-register, and collect data.

    This handles the case where a previous registration left behind
    a stale machine-id that causes insights-client to fail.

    Args:
        client: ContentHost instance to clean up

    Returns:
        Result of the final insights-client command (data collection/upload)
    """
    client.execute('insights-client --unregister')
    client.execute('rm -f /etc/insights-client/machine-id')
    client.execute('rm -f /etc/insights-client/.registered')
    client.execute('insights-client --register')
    # Run insights-client again to collect and upload data after re-registration
    return client.execute('insights-client')


def sync_rhel_content(satellite, organization, rhel_versions):
    """Enable and synchronously sync RHEL repos for the given major versions.

    Syncs the BaseOS and AppStream repositories each pinned vulnerable
    package in ``VULNERABLE_PACKAGES`` can be installed from.

    Args:
        satellite: Satellite instance to enable and sync the repositories on.
        organization: Organization to enable the repositories in.
        rhel_versions: Iterable of RHEL major versions, e.g. ``(9,)``.
    """
    for rhel_ver in rhel_versions:
        for repo_type in ('bos', 'aps'):
            name = f'rhel{rhel_ver}_{repo_type}'
            if name not in REPOS:
                continue
            rh_repo_id = satellite.api_factory.enable_rhrepo_and_fetchid(
                basearch=DEFAULT_ARCHITECTURE,
                org_id=organization.id,
                product=REPOS[name]['product'],
                repo=REPOS[name]['name'],
                reposet=REPOS[name]['reposet'],
                releasever=REPOS[name]['releasever'],
            )

            rh_repo = satellite.api.Repository(id=rh_repo_id).read()
            task = rh_repo.sync(synchronous=False)
            satellite.wait_for_tasks(
                search_query=(f'id = {task["id"]}'),
                poll_timeout=2500,
                must_succeed=False,
            )
            task_status = satellite.api.ForemanTask(id=task['id']).poll()
            assert task_status['result'] == 'success'


def prepare_vulnerable_host(client):
    """Install a pinned vulnerable package on a host and upload the insights archive.

    The package picked per RHEL version from ``VULNERABLE_PACKAGES`` is
    guaranteed to report known CVEs once the Vulnerability Engine evaluates
    the uploaded archive.

    Args:
        client: Content host registered with insights (see ``enable_insights``).

    Returns:
        The same content host instance.
    """
    rhel_ver = client.os_version.major
    vuln_data = VULNERABLE_PACKAGES[rhel_ver]
    assert vuln_data['rpm'], f'No vulnerable package defined for RHEL {rhel_ver}'

    assert (
        client.execute(
            'find /etc/yum.repos.d/ -type f | grep -vF redhat.repo | xargs -I \'{}\' rm \'{}\''
        ).status
        == 0
    )
    update_result = client.execute('dnf -y update')
    if update_result.status != 0:
        # Some RHEL snapshots can have transient dependency resolution conflicts.
        # Retry with safer solver flags to keep fixture setup stable.
        update_result = client.execute('dnf -y update --nobest --allowerasing')
    assert update_result.status == 0, (
        f'Failed to update packages before vulnerability setup: '
        f'{update_result.stdout}\n{update_result.stderr}'
    )
    # Install vulnerable package version for the host's RHEL version
    assert client.execute(f'dnf install -y {vuln_data["rpm"]}').status == 0
    # Run insights-client to report the vulnerabilities to Satellite
    result = client.execute('insights-client')
    if result.status != 0 and 'Machine-id found' in result.stdout:
        result = cleanup_stale_insights_state(client)
    assert result.status == 0, f'insights-client failed: {result.stdout}'
    return client


@pytest.fixture
def vulnerable_rhel_host(rhel_insights_vm):
    """A function-level fixture to prepare a RHEL host with a vulnerable package"""
    return prepare_vulnerable_host(rhel_insights_vm)


@pytest.fixture
def vulnerable_rhel_host_with_recommendations(vulnerable_rhel_host):
    """A fixture to prepare a RHEL host with both vulnerabilities and recommendations.

    Extends vulnerable_rhel_host by adding file permission misconfiguration
    to trigger a recommendation.
    """
    client = vulnerable_rhel_host
    # Add permission misconfiguration to create a recommendation.
    assert client.execute('chmod 777 /etc/shadow').status == 0
    # Run insights-client to report the recommendation to Satellite
    result = client.execute('insights-client')
    assert result.status == 0, f'insights-client failed: {result.stdout}'
    return client


@pytest.fixture(scope='module')
def module_vulnerable_insights_host(
    module_target_sat_insights,
    rhcloud_manifest_org,
    rhcloud_activation_key,
    module_rhel_contenthost,
):
    """A module-level fixture providing a vulnerable insights-registered RHEL host.

    Syncs the RHEL content for the host's version into the manifest
    organization (so the pinned vulnerable package can be installed), starts
    the IoP CVE feed sync services, enables insights on the host, and finally
    installs the vulnerable package and uploads the insights archive for the
    Vulnerability Engine to evaluate. Unlike the function-scoped
    ``vulnerable_rhel_host`` the host is provisioned once per test module.
    """
    satellite = module_target_sat_insights
    client = module_rhel_contenthost
    rhel_ver = client.os_version.major

    sync_rhel_content(satellite, rhcloud_manifest_org, (rhel_ver,))
    # Manually trigger CVE sync and wait for completion.
    trigger_cve_sync(satellite, assert_start=True)
    enable_insights(client, satellite, rhcloud_manifest_org, rhcloud_activation_key)
    return prepare_vulnerable_host(client)
