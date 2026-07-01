"""Smoke tests to check installation health

:Requirement: Installation

:CaseAutomation: Automated

:CaseComponent: Installation

:Team: Rocket

:CaseImportance: Critical

"""

from broker import Broker
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from fauxfactory import gen_string
import pytest

from robottelo.cli import hammer
from robottelo.config import settings
from robottelo.constants import (
    FOREMANCTL_PARAMETERS_FILE,
    FOREMANCTL_POSTGRESQL_TUNING_PROFILES,
    InstallationServices,
)
from robottelo.hosts import Satellite
from robottelo.utils.issue_handlers import is_open

pytestmark = [pytest.mark.foremanctl, pytest.mark.upgrade]

FOREMANCTL_CERTS_DIR = '/var/lib/foremanctl/certs/certs'


def common_sat_install_assertions(satellite):
    # no errors/failures in journald
    result = satellite.execute(
        r'journalctl --quiet --no-pager --boot --grep ERROR -u "dynflow-sidekiq*" -u "foreman-proxy" -u "foreman" -u "httpd" -u "postgresql" -u "pulp-api" -u "pulp-content" -u "pulp-worker*" -u "valkey" -u "candlepin"'
    )
    if is_open('SAT-21086'):
        assert not list(filter(lambda x: 'PG::' not in x, result.stdout.splitlines()))
    else:
        assert not result.stdout
    # no errors/failures in /var/log/httpd/*
    result = satellite.execute(r'grep -iR "error" /var/log/httpd/*')
    assert not result.stdout
    httpd_log = satellite.execute('journalctl --unit=httpd')
    assert 'WARNING' not in httpd_log.stdout


def assert_hammer_ping_ok(result):
    assert result.status == 0, 'hammer ping failed'
    services = hammer.parse_ping(result.stdout)
    for status in services.values():
        assert status == 'ok'


def assert_postgresql_tuning(sat, tuning):
    expected_pg = FOREMANCTL_POSTGRESQL_TUNING_PROFILES[tuning]
    for pg_setting, expected_value in expected_pg.items():
        result = sat.execute(
            f'podman exec postgresql psql -U postgres -t -A -c "show {pg_setting};"'
        )
        actual_value = result.stdout.strip()
        assert actual_value == expected_value, (
            f'Expected {pg_setting}={expected_value}, got {actual_value}'
        )


@pytest.fixture(scope='module')
def module_sat_ready_rhel(request):
    param = request.param
    deploy_args = param.get('deploy_args', '') if isinstance(param, dict) else ''
    with Broker(
        workflow=settings.server.deploy_workflows.os,
        deploy_rhel_version=settings.server.version.rhel_version,
        deploy_flavor=settings.flavors.default,
        deploy_network_type=settings.server.network_type,
        host_class=Satellite,
    ) as sat:
        sat.install_satellite_foremanctl(
            enable_fapolicyd=(param == 'fapolicyd'),
            enable_fips=(param == 'fips'),
            parameters=deploy_args,
        )
        yield sat


@pytest.fixture(scope='module')
def module_sat_foremanctl_tuning(request):
    # Deploy rhel to install foremanctl with different tuning profiles
    with Broker(
        workflow=settings.server.deploy_workflows.os,
        deploy_rhel_version=settings.server.version.rhel_version,
        deploy_flavor=settings.flavors.large,
        deploy_network_type=settings.server.network_type,
        host_class=Satellite,
    ) as sat:
        sat.install_satellite_foremanctl(
            parameters=[
                f'--tuning {request.param}',
            ]
        )
        yield sat


@pytest.mark.first_sanity
@pytest.mark.parametrize('module_sat_ready_rhel', ['default'], indirect=True)
def test_satellite_installation_with_foremanctl(module_sat_ready_rhel):
    """Run a basic Satellite installation

    :id: 661206f3-2eec-403c-af26-3c5cadcd5769

    :steps:
        1. Get RHEL Host
        2. Configure satellite repos
        3. Install satellite using foremanctl
        4. Run foremanctl deploy

    :expectedresults:
        1. foremanctl deploy runs successfully
        2. no unexpected errors in logs
    """
    common_sat_install_assertions(module_sat_ready_rhel)


@pytest.mark.parametrize('module_sat_ready_rhel', ['default'], indirect=True)
@pytest.mark.parametrize('service', InstallationServices.FOREMANCTL_SERVICES)
def test_positive_check_installer_service_running(service, module_sat_ready_rhel):
    """Check if all Satellite services is running

    :id: 5389c174-7ab1-4e9d-b2aa-66d80fd6dc5h

    :steps:
        1. Verify a service is active with systemctl is-active

    :expectedresults: All Satellite services are active
    """
    is_active = module_sat_ready_rhel.execute(f'systemctl is-active {service}')
    status = module_sat_ready_rhel.execute(f'systemctl status {service}')
    assert is_active.status == 0, status.stdout


@pytest.mark.parametrize('module_sat_ready_rhel', ['default'], indirect=True)
def test_positive_check_installer_hammer_ping(module_sat_ready_rhel):
    """Check if hammer ping reports all services as ok

    :id: 85fd4388-6d94-42f5-bed2-24be38e9f111

    :steps:
        1. Run the 'hammer ping' command on satellite.

    :expectedresults: All services are active (running)
    """
    # check status reported by hammer ping command
    result = module_sat_ready_rhel.execute('hammer ping')
    assert_hammer_ping_ok(result)


@pytest.fixture(scope='module')
def module_sat_foremanctl_custom_certs():
    with Broker(
        workflow=settings.server.deploy_workflows.os,
        deploy_rhel_version=settings.server.version.rhel_version,
        deploy_flavor=settings.flavors.default,
        deploy_network_type=settings.server.network_type,
        host_class=Satellite,
    ) as sat:
        sat.custom_cert_generate(sat.hostname)
        sat.install_satellite_foremanctl(
            parameters=[
                '--certificate-source=custom_server',
                f'--certificate-server-certificate /root/{sat.hostname}/{sat.hostname}.crt',
                f'--certificate-server-key /root/{sat.hostname}/{sat.hostname}.key',
                '--certificate-server-ca-certificate /root/cacert.crt',
            ]
        )
        yield sat


@pytest.mark.e2e
def test_positive_install_foremanctl_with_custom_certs(module_sat_foremanctl_custom_certs):
    """Install Satellite via foremanctl deploy with custom certificates.

    :id: aca40725-8884-454e-8a67-428ce3292660

    :steps:
        1. Generate custom CA and server certificates
        2. Install Satellite using foremanctl deploy with custom cert flags
        3. Assert all services are running
        4. Assert custom ca certificate works and there are no errors

    :expectedresults: Satellite is installed with custom certs and all services are healthy.

    :CaseAutomation: Automated
    """
    sat = module_sat_foremanctl_custom_certs
    common_sat_install_assertions(sat)
    # check the services are up and healthy
    result = sat.execute('hammer ping')
    assert_hammer_ping_ok(result)
    # Verify the custom certificate works and there are no errors
    result = sat.execute(
        'curl --output /dev/null --write-out "%{http_code}" --cacert /root/cacert.crt '
        f'https://{sat.hostname}/api/v2/ping'
    )
    assert result.stdout == '200', f'Calling API with custom cert failed: {result.stderr}'


@pytest.mark.parametrize('module_sat_ready_rhel', ['default'], indirect=True)
def test_foremanctl_deploy_reset_parameters(module_sat_ready_rhel):
    """Check if foremanctl deploy --reset parameters works

    :id: 661206f3-2eec-403c-af26-3c5caaaa5769

    :steps:
        1. Install Satellite with foremanctl deploy with parameters
        2. Verify foreman_puma_workers and pulp_worker_count are set to 2
        3. Reset foreman_puma_workers and pulp_worker_count
        4. Verify foreman_puma_workers and pulp_worker_count are not set

    :expectedresults:
        1. foremanctl deploy with parameters runs successfully
        2. foreman_puma_workers and pulp_worker_count are set to 2
        3. foreman_puma_workers and pulp_worker_count are not set
    """

    assert (
        module_sat_ready_rhel.execute(
            'foremanctl deploy --pulp-worker-count 2 --foreman-puma-workers 2',
            timeout='30m',
        ).status
        == 0
    )

    parameters_file = module_sat_ready_rhel.load_remote_yaml_file(FOREMANCTL_PARAMETERS_FILE)
    assert parameters_file.foreman_puma_workers == '2'
    assert parameters_file.pulp_worker_count == '2'

    assert (
        module_sat_ready_rhel.execute(
            'foremanctl deploy --reset-foreman-puma-workers --reset-pulp-worker-count'
        ).status
        == 0
    )

    parameters_file = module_sat_ready_rhel.load_remote_yaml_file(FOREMANCTL_PARAMETERS_FILE)
    assert 'foreman_puma_workers' not in parameters_file
    assert 'pulp_worker_count' not in parameters_file


@pytest.mark.parametrize('module_sat_ready_rhel', ['default'], indirect=True)
def test_foremanctl_deploy_certificate_cname(module_sat_ready_rhel):
    """Verify foremanctl deploy --certificate-cname adds CNAME to server certificate SANs

    :id: a5390e11-0e48-4a13-951f-749df8716e0c

    :steps:
        1. Run foremanctl deploy --certificate-cname with an additional DNS name
        2. Verify HTTPS connectivity using the CNAME with the self-signed CA

    :expectedresults:
        1. foremanctl deploy completes successfully
        2. HTTPS request via the CNAME returns HTTP 200 without certificate errors
    """
    satellite = module_sat_ready_rhel
    cname = f'cname.{satellite.hostname}'

    result = satellite.execute(
        f'foremanctl deploy --certificate-cname {cname}',
        timeout='10m',
    )
    assert result.status == 0, (
        f'foremanctl deploy with --certificate-cname failed:\n{result.stderr}'
    )

    result = satellite.execute(
        'curl --fail --silent --show-error --head '
        f'--cacert {FOREMANCTL_CERTS_DIR}/ca.crt '
        f'--resolve "{cname}:443:127.0.0.1" '
        f'https://{cname}/users/login'
    )
    assert result.status == 0, f'HTTPS request failed for {cname}:\n{result.stderr}'
    assert '200 OK' in result.stdout, (
        f'Expected HTTP 200 response for {cname}.\nOutput:\n{result.stdout}'
    )


def get_cert_validity_days(sat, cert_path):
    """Get the total validity period in days for a certificate file.

    Calculates the difference between Before and After dates.
    """
    result = sat.execute(
        f'start=$(date -d "$(openssl x509 -in {cert_path} -noout -startdate | cut -d= -f2)" +%s)'
        f' && end=$(date -d "$(openssl x509 -in {cert_path} -noout -enddate | cut -d= -f2)" +%s)'
        ' && echo $(( (end - start) / 86400 ))'
    )
    assert result.status == 0, f'Failed to read certificate at {cert_path}: {result.stderr}'
    return int(result.stdout.strip())


def get_cert_fingerprint(sat, cert_path):
    """Get the SHA256 fingerprint of a certificate, used to track certificate identity."""
    result = sat.execute(f'openssl x509 -in {cert_path} -noout -fingerprint -sha256')
    assert result.status == 0, f'Failed to get fingerprint for {cert_path}: {result.stderr}'
    return result.stdout.strip()


def cert_fingerprint_openssl_sha256(cert):
    """SHA256 fingerprint line matching ``openssl x509 -noout -fingerprint -sha256``."""
    digest = cert.fingerprint(hashes.SHA256())
    return 'sha256 Fingerprint=' + ':'.join(f'{b:02X}' for b in digest)


custom_ca_days = 3650
custom_cert_days = 365


@pytest.mark.parametrize(
    'module_sat_ready_rhel',
    [
        {
            'deploy_args': [
                f'--certificate-ca-validity-days {custom_ca_days}',
                f'--certificate-validity-days {custom_cert_days}',
            ],
        }
    ],
    indirect=True,
)
def test_positive_foremanctl_certificate_custom_validity_and_renewal(module_sat_ready_rhel):
    """Verification of certificate expiry parameters introduced
    in foremanctl PR#456: validates parameter persistence in the answers file,
    certificate chain integrity, certificate identity through renewals via
    fingerprint tracking, and API health.

    :id: c7e3a5b1-4d2f-48e6-9a1c-5f8d2b7e0c43

    :steps:
        1. Deploy with custom CA validity (3650d) and cert validity (365d)
        2. Verify parameters file persists certificates_ca_validity_days and
           certificates_validity_days with the correct values
        3. Verify CA subject contains 'Foreman Self-signed CA'
        4. Verify server and client certs are signed by the CA (chain validation)
        5. Capture SHA256 fingerprints of CA, server, and client certificates
        6. Verify Katello API ping and CRUD via nailgun
        7. Renew with --certificate-renew --certificate-validity-days 730
        8. Verify certificates_renew is NOT persisted (one-shot flag, persist: false)
        9. Verify certificates_validity_days IS updated to 730 in parameters file
        10. Verify CA fingerprint is unchanged (CA was not regenerated)
        11. Verify server/client fingerprints changed (certs were regenerated)
        12. Verify renewed certs are still signed by the same CA
        13. Verify renewed cert validity and API health

    :expectedresults:
        1. Parameters file persists validity values but not the renewal flag
        2. The certificate chain integrity maintained throughout the renewal process
        3. Only server/client certs are regenerated, CA identity preserved
        4. API remains healthy and functional after all certificate operations

    :Verifies: SAT-43479

    :CaseAutomation: Automated
    """
    sat = module_sat_ready_rhel
    ca_cert = f'{FOREMANCTL_CERTS_DIR}/ca.crt'
    server_cert = f'{FOREMANCTL_CERTS_DIR}/{sat.hostname}.crt'
    client_cert = f'{FOREMANCTL_CERTS_DIR}/{sat.hostname}-client.crt'

    renewed_cert_days = 730

    # Phase 1: Deploy with custom validity
    result = sat.execute(
        f'foremanctl deploy'
        f' --certificate-ca-validity-days {custom_ca_days}'
        f' --certificate-validity-days {custom_cert_days}',
        timeout='30m',
    )
    assert result.status == 0, f'Deploy with custom validity failed: {result.stderr}'

    # Verify parameter persistence in the answers file
    params = sat.load_remote_yaml_file(FOREMANCTL_PARAMETERS_FILE)
    assert str(params.certificates_ca_validity_days) == str(custom_ca_days), (
        f'certificates_ca_validity_days not persisted correctly: {params.certificates_ca_validity_days}'
    )
    assert str(params.certificates_validity_days) == str(custom_cert_days), (
        f'certificates_validity_days not persisted correctly: {params.certificates_validity_days}'
    )

    # Verify CA subject matches the Ansible template subject
    ca_subject = sat.execute(f'openssl x509 -in {ca_cert} -noout -subject')
    assert ca_subject.status == 0
    assert 'Foreman Self-signed CA' in ca_subject.stdout, (
        f'CA subject does not contain expected subject: {ca_subject.stdout}'
    )

    # Verify certificate chain — server and client signed by CA
    for cert in (server_cert, client_cert):
        verify = sat.execute(f'openssl verify -CAfile {ca_cert} {cert}')
        assert verify.status == 0, f'Chain validation failed for {cert}: {verify.stderr}'

    # Capture fingerprints to track certificate identity across renewal
    ca_fp_before = get_cert_fingerprint(sat, ca_cert)
    server_fp_before = get_cert_fingerprint(sat, server_cert)
    client_fp_before = get_cert_fingerprint(sat, client_cert)

    # Verify certificate validity periods
    assert get_cert_validity_days(sat, ca_cert) == custom_ca_days
    assert get_cert_validity_days(sat, server_cert) == custom_cert_days
    assert get_cert_validity_days(sat, client_cert) == custom_cert_days

    # API: Verify services are healthy
    result = sat.execute('hammer ping')
    assert_hammer_ping_ok(result)

    # API: Verify operations work over TLS with custom-validity certs
    org_name = gen_string('alpha')
    org = sat.api.Organization(name=org_name).create()
    assert org.name == org_name

    # Phase 2: Renew server/client certs with different validity
    result = sat.execute(
        f'foremanctl deploy --certificate-renew --certificate-validity-days {renewed_cert_days}',
        timeout='30m',
    )
    assert result.status == 0, f'Certificate renewal failed: {result.stderr}'

    # Certificates_renew must NOT be persisted (persist: false in metadata)
    params = sat.load_remote_yaml_file(FOREMANCTL_PARAMETERS_FILE)
    assert 'certificates_renew' not in params, (
        'certificates_renew was persisted but metadata defines persist: false'
    )

    # Certificates_validity_days must be updated to renewed value
    assert str(params.certificates_validity_days) == str(renewed_cert_days), (
        f'certificates_validity_days not updated after renewal: {params.certificates_validity_days}'
    )

    # CA certificate fingerprint must be unchanged (CA not regenerated)
    ca_fp_after = get_cert_fingerprint(sat, ca_cert)
    assert ca_fp_after == ca_fp_before, (
        'CA fingerprint changed after --certificate-renew; CA should not be regenerated'
    )

    foreman_ca_pem = sat.get_foreman_raw_ca(verify=False)
    foreman_ca_certs = x509.load_pem_x509_certificates(foreman_ca_pem.encode())
    foreman_ca_fps = {cert_fingerprint_openssl_sha256(c) for c in foreman_ca_certs}
    assert ca_fp_after in foreman_ca_fps, (
        'CA from GET /unattended/public/foreman_raw_ca does not match on-disk foremanctl CA'
    )

    # Server/client fingerprints must differ (force: certificates_renew | bool)
    server_fp_after = get_cert_fingerprint(sat, server_cert)
    client_fp_after = get_cert_fingerprint(sat, client_cert)
    assert server_fp_after != server_fp_before, (
        'Server cert fingerprint unchanged — renewal did not regenerate it'
    )
    assert client_fp_after != client_fp_before, (
        'Client cert fingerprint unchanged — renewal did not regenerate it'
    )

    # Verify the server certificate presented by the TLS socket matches the on-disk server certificate
    presented_server_pem = sat.get_server_certificate_from_ssl_socket()
    presented_server_cert = x509.load_pem_x509_certificate(presented_server_pem.encode())
    assert cert_fingerprint_openssl_sha256(presented_server_cert) == server_fp_after, (
        'TLS-presented server certificate fingerprint does not match on-disk server cert'
    )

    # Renewed certs must still chain to the same CA
    for cert in (server_cert, client_cert):
        verify = sat.execute(f'openssl verify -CAfile {ca_cert} {cert}')
        assert verify.status == 0, (
            f'Chain validation failed after renewal for {cert}: {verify.stderr}'
        )

    # Verify renewed validity periods, CA unchanged
    assert get_cert_validity_days(sat, server_cert) == renewed_cert_days
    assert get_cert_validity_days(sat, client_cert) == renewed_cert_days
    assert get_cert_validity_days(sat, ca_cert) == custom_ca_days

    # API: Verify services remain healthy after renewal
    result = sat.execute('hammer ping')
    assert_hammer_ping_ok(result)

    # API: Verify CRUD still works with renewed certificates
    org = sat.api.Organization(id=org.id).read()
    assert org.name == org_name


@pytest.mark.e2e
@pytest.mark.parametrize('module_sat_ready_rhel', ['default'], indirect=True)
def test_foremanctl_deploy_add_remove_feature(module_sat_ready_rhel):
    """Verify foremanctl deploy --add-feature and --remove-feature work correctly.

    :id: ec1e8b03-5b29-450a-887d-3a75ab707336

    :steps:
        1. Deploy Satellite with remote-execution feature
        2. Verify the remote-execution feature is enabled
        3. Remove 'remote-execution' feature
        4. Verify the remote-execution feature is disabled

    :expectedresults:
        1. The remote-execution feature is enabled
        2. The remote-execution feature is disabled
    """
    FEATURE_NAME = 'remote-execution'
    sat = module_sat_ready_rhel
    result = sat.execute(
        f'foremanctl deploy --add-feature {FEATURE_NAME}',
        timeout='30m',
    )
    assert result.status == 0, (
        f'foremanctl deploy --add-feature {FEATURE_NAME} failed: {result.stderr}'
    )

    assert FEATURE_NAME in sat.list_foremanctl_features(enabled=True), (
        f'{FEATURE_NAME} is not enabled'
    )

    result = sat.execute(f'foremanctl deploy --remove-feature {FEATURE_NAME}', timeout='30m')
    assert result.status == 0, (
        f'foremanctl deploy --remove-feature {FEATURE_NAME} failed: {result.stderr}'
    )

    assert FEATURE_NAME not in sat.list_foremanctl_features(enabled=True), (
        f'{FEATURE_NAME} is still enabled'
    )


@pytest.mark.parametrize('module_sat_foremanctl_tuning', ['medium'], indirect=True)
def test_positive_foremanctl_tuning_profile(module_sat_foremanctl_tuning):
    """Verify foremanctl deploy with a tuning profile applies successfully

    :id: f55e8a14-eb93-4416-82ee-f389b3bbd768

    :steps:
        1. Install Satellite with foremanctl deploy with the 'medium' tuning profile
        2. Verify the tuning parameter is recorded in the parameters file
        3. Verify PostgreSQL settings match the medium profile
        4. Reset tuning back to 'default'
        5. Verify the default profile is recorded
        6. Verify PostgreSQL settings match the default profile

    :expectedresults:
        1. foremanctl deploy --tuning medium succeeds
        2. The parameters file records tuning as 'medium'
        3. PostgreSQL max_connections, shared_buffers, effective_cache_size match medium profile
        4. foremanctl deploy --tuning default succeeds
        5. The parameters file records tuning as 'default'
        6. PostgreSQL settings revert to default values

    :CaseAutomation: Automated
    """
    sat = module_sat_foremanctl_tuning
    # verify foremanctl is deployed with medium tuning profile
    parameters_file = sat.load_remote_yaml_file(FOREMANCTL_PARAMETERS_FILE)
    assert parameters_file.tuning == 'medium'
    assert_postgresql_tuning(sat, 'medium')

    # reset tuning back to default
    assert (
        sat.execute(
            'foremanctl deploy --reset-tuning',
            timeout='30m',
        ).status
        == 0
    )

    parameters_file = sat.load_remote_yaml_file(FOREMANCTL_PARAMETERS_FILE)
    assert 'tuning' not in parameters_file
    assert_postgresql_tuning(sat, 'default')
