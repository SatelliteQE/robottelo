"""Test class for ``katello-certs-check``.

:Requirement: katello-certs-check

:CaseAutomation: Automated

:CaseLevel: System

:CaseComponent: Certificates

:Assignee: okhatavk

:TestType: Functional

:CaseImportance: High

:Upstream: No

"""
import re

import pytest

import robottelo.constants as constants
from robottelo.config import settings
from robottelo.utils.issue_handlers import is_open

pytestmark = pytest.mark.destructive


def test_positive_update_katello_certs(cert_setup_destructive_teardown):
    """Update certificates on a currently running satellite instance.

    :id: 0ddf6954-dc83-435e-b156-b567b877c2a5

    :steps:

        1. Use Jenkins provided custom certs
        2. Assert hammer ping reports running Satellite
        3. Update satellite with custom certs
        4. Assert output does not report SSL certificate error
        5. Assert all services are running


    :expectedresults: Katello-certs should be updated.

    :CaseAutomation: Automated
    """
    try:
        cert_data, satellite = cert_setup_destructive_teardown
        result = satellite.execute('hammer ping')
        assert result.status == 0, f'Hammer Ping failed:\n{result.stderr}'
        command = (
            'satellite-installer --scenario satellite '
            f'--certs-server-cert "/root/{cert_data["cert_file_name"]}" '
            f'--certs-server-key "/root/{cert_data["key_file_name"]}" '
            f'--certs-server-ca-cert "/root/{cert_data["ca_bundle_file_name"]}" '
            '--certs-update-server --certs-update-server-ca'
        )
        result = satellite.execute(command)
        assert result.status == 0
        # assert no hammer ping SSL cert error
        result = satellite.execute('hammer ping')
        assert 'SSL certificate verification failed' not in result.stdout
        assert result.stdout.count('ok') == 8
        # assert all services are running
        result = satellite.execute('satellite-maintain health check --label services-up -y')
        assert result.status == 0, 'Not all services are running'
    finally:
        # revert to original certs
        command = 'satellite-installer --scenario satellite --certs-reset'
        result = satellite.execute(command)
        assert result.status == 0
        # Check for hammer ping SSL cert error
        result = satellite.execute('hammer ping')
        assert result.status == 0, f'Hammer Ping failed:\n{result.stderr}'
        # assert all services are running
        result = satellite.execute('satellite-maintain health check --label services-up -y')
        assert result.status == 0, 'Not all services are running'


@pytest.mark.parametrize(
    'certs_vm_setup',
    [
        {'nick': 'rhel7', 'target_memory': '20GiB', 'target_cores': 4},
        {'nick': 'rhel8', 'target_memory': '20GiB', 'target_cores': 4},
    ],
    ids=['rhel7', 'rhel8'],
    indirect=True,
)
def test_positive_install_sat_with_katello_certs(certs_vm_setup):
    """Update certificates on a currently running satellite instance.

    :id: 47e3a57f-d7a2-40d2-bbc7-d1bb3d79a7e1

    :steps:

        1. Generate the custom certs on RHEL 7 machine
        2. Install satellite with custom certs
        3. Assert output does not report SSL certificate error
        4. Assert all services are running


    :expectedresults: Satellite should be installed using the custom certs.

    :CaseAutomation: Automated
    """
    cert_data, rhel_vm = certs_vm_setup
    version = rhel_vm.os_version.major
    rhel_vm.download_repos(repo_name='satellite', version=version)
    rhel_vm.register_contenthost(
        org=None,
        lce=None,
        username=settings.subscription.rhn_username,
        password=settings.subscription.rhn_password,
    )
    result = rhel_vm.subscription_manager_attach_pool([settings.subscription.rhn_poolid])[0]
    for repo in getattr(constants, f"OHSNAP_RHEL{version}_REPOS"):
        rhel_vm.enable_repo(repo, force=True)
    # What is the purpose of this?
    rhel_vm.execute(
        f'yum -y localinstall {settings.repos.dogfood_repo_host}'
        f'/pub/katello-ca-consumer-latest.noarch.rpm'
    )
    rhel_vm.execute('yum -y update')
    result = rhel_vm.execute(getattr(constants, f"INSTALL_RHEL{version}_STEPS"))
    assert result.status == 0
    command = (
        'satellite-installer --scenario satellite '
        f'--certs-server-cert "/root/{cert_data["cert_file_name"]}" '
        f'--certs-server-key "/root/{cert_data["key_file_name"]}" '
        f'--certs-server-ca-cert "/root/{cert_data["ca_bundle_file_name"]}" '
    )
    result = rhel_vm.execute(command, timeout=2200000)
    assert result.status == 0
    # assert no hammer ping SSL cert error
    result = rhel_vm.execute('hammer ping')
    assert 'SSL certificate verification failed' not in result.stdout
    assert result.stdout.count('ok') == 8
    # assert all services are running
    result = rhel_vm.execute('satellite-maintain health check --label services-up -y')
    assert result.status == 0, 'Not all services are running'


def test_regeneration_ssl_build_certs(target_sat):
    """delete the ssl-build folder and cross check that ssl-build folder is
    recovered/regenerated after running the installer

    :id: becdc758-44ed-4d6d-ac60-2f5c5b14278f

    :steps:

        1. remove the ssl-build folder which holds all certificates
        2. run the installer to regenerate / recover the ssl-build with certs
        3. Assert certs are generated in the ssl-build

    :expectedresults: ssl-build folder is regenerated with certs.

    :CaseAutomation: Automated
    """
    result = target_sat.execute('hammer ping')
    assert result.status == 0, f'Hammer Ping failed:\n{result.stderr}'
    target_sat.execute('rm -rf /root/ssl-build')
    result = target_sat.execute('satellite-installer --scenario satellite', timeout=2200000)
    assert result.status == 0
    target_sat.execute("ls -ltr /root | grep 'ssl-build'")
    assert result.status == 0, f'ssl-build certs generation failed:\n{result.stderr}'
    # assert no hammer ping SSL cert error
    result = target_sat.execute('hammer ping')
    assert 'SSL certificate verification failed' not in result.stdout
    assert result.stdout.count('ok') == 8
    # assert all services are running
    result = target_sat.execute('satellite-maintain health check --label services-up -y')
    assert result.status == 0, 'Not all services are running'


def test_positive_generate_capsule_certs_using_absolute_path(cert_setup_destructive_teardown):
    """Create Capsule certs using absolute paths.

    :id: 72024757-be6f-49f0-8b88-c57c83f5e7e9

    :steps:

        1. Use Certificates generated in class setup
        2. Run capsule-certs-generate with custom certs and absolute path
           for --certs-tar
        3. Assert the certs tar file was created.
        4. Assert include cname in certificates when specified --foreman-proxy-cname'

    :expectedresults: Capsule certs are generated.

    :customerscenario: true

    :BZ: 1466688, 1899108, 1857176

    :CaseAutomation: Automated
    """
    cert_data, satellite = cert_setup_destructive_teardown
    satellite.execute('mkdir -p /root/capsule_cert')
    satellite.execute(
        f'cp {cert_data["ca_bundle_file_name"]} /root/capsule_cert/ca_cert_bundle.pem'
    )
    satellite.execute(f'cp {cert_data["cert_file_name"]} /root/capsule_cert/capsule_cert.pem')
    satellite.execute(f'cp {cert_data["key_file_name"]} /root/capsule_cert/capsule_cert_key.pem')
    result = satellite.execute(
        'capsule-certs-generate '
        f'--foreman-proxy-fqdn {cert_data["capsule_hostname"]} '
        '--certs-tar /root/capsule_cert/capsule_certs_Abs.tar '
        '--server-cert /root/capsule_cert/capsule_cert.pem '
        '--server-key /root/capsule_cert/capsule_cert_key.pem '
        '--server-ca-cert /root/capsule_cert/ca_cert_bundle.pem '
        '--foreman-proxy-cname capsule.example1.com '
        '--certs-update-server'
    )
    assert result.status == 0, 'Capsule certs generate script failed.'
    # assert include cname in certificates when specified --foreman-proxy-cname'
    result = satellite.execute(
        'openssl x509 -in /root/ssl-build/capsule.example.com/'
        'capsule.example.com-foreman-client.crt -text | '
        'grep capsule.example1.com'
    )
    assert 'DNS:capsule.example1.com' in result.stdout
    # assert the certs.tar was built
    assert satellite.execute('test -e /root/capsule_cert/capsule_certs_Abs.tar')


@pytest.mark.upgrade
def test_positive_generate_capsule_certs_using_relative_path(cert_setup_destructive_teardown):
    """Create Capsule certs using relative paths.

    :id: 50df0b87-d2d3-42fb-86d5-988ebaaa9ba3

    :steps:

        1. Use Certificates generated in class setup
        2. Run capsule-certs-generate with custom certs and relative path
           for --certs-tar
        3. Assert the certs tar file was created.

    :expectedresults: Capsule certs are generated.

    :BZ: 1466688, 1899108

    :CaseAutomation: Automated
    """
    cert_data, satellite = cert_setup_destructive_teardown
    satellite.execute('mkdir -p /root/capsule_cert')
    satellite.execute(
        f'cp "{cert_data["ca_bundle_file_name"]}" /root/capsule_cert/ca_cert_bundle.pem'
    )
    satellite.execute(f'cp "{cert_data["cert_file_name"]}" /root/capsule_cert/capsule_cert.pem')
    satellite.execute(f'cp "{cert_data["key_file_name"]}" /root/capsule_cert/capsule_cert_key.pem')
    result = satellite.execute(
        'capsule-certs-generate '
        f'--foreman-proxy-fqdn {cert_data["capsule_hostname"]} '
        '--certs-tar ~/capsule_cert/capsule_certs_Rel.tar '
        '--server-cert ~/capsule_cert/capsule_cert.pem '
        '--server-key ~/capsule_cert/capsule_cert_key.pem '
        '--server-ca-cert ~/capsule_cert/ca_cert_bundle.pem '
        '--certs-update-server',
    )
    assert result.status == 0, 'Capsule certs generate script failed.'
    # assert the certs.tar was built
    assert satellite.execute('test -e root/capsule_cert/capsule_certs_Rel.tar')


@pytest.mark.tier1
def test_positive_validate_capsule_certificate(capsule_certs_teardown):
    """Check that Capsules cert handles additional proxy names.

    :id: 8b53fc3d-704f-44f4-899e-74654529bfcf

    :customerscenario: true

    :steps:

        1. Generate a Capsule certificate
        2. Confirm proxy server's FQDN for DNS is present
        3. Confirm that format of alternative names does not include []

    :expectedresults: Capsule certs has valid DNS values

    :BZ: 1747581

    :CaseAutomation: Automated
    """
    file_setup, target_sat = capsule_certs_teardown
    DNS_Check = False
    # extract the cert from the tar file
    result = target_sat.execute(
        f'tar -xf {file_setup["tmp_dir"]}/capsule_certs.tar '
        f'--directory {file_setup["tmp_dir"]}/ '
    )
    assert result.status == 0, 'Extraction to working directory failed.'
    # Extract raw data from RPM to a file
    target_sat.execute(
        'rpm2cpio {0}/ssl-build/{1}/'
        '{1}-qpid-router-server*.rpm'
        '>> {0}/ssl-build/{1}/cert-raw-data'.format(
            file_setup['tmp_dir'], file_setup['capsule_hostname']
        )
    )
    # Extract the cert data from file cert-raw-data and write to cert-data
    target_sat.execute(
        'openssl x509 -noout -text -in {0}/ssl-build/{1}/cert-raw-data'
        '>> {0}/ssl-build/{1}/cert-data'.format(
            file_setup['tmp_dir'], file_setup['capsule_hostname']
        )
    )
    # use same location on remote and local for cert_file
    target_sat.get(file_setup['caps_cert_file'])
    # search the file for the line with DNS
    with open(file_setup['caps_cert_file']) as file:
        for line in file:
            if re.search(r'\bDNS:', line):
                match = re.search(r'{}'.format(file_setup['capsule_hostname']), line)
                assert match, 'No proxy name found.'
                if is_open('BZ:1747581'):
                    DNS_Check = True
                else:
                    match = re.search(r'\[]', line)
                    assert not match, 'Incorrect parsing of alternative proxy name.'
                    DNS_Check = True
                break
            # if no match for "DNS:" found, then raise error.
    assert DNS_Check, 'Cannot find Subject Alternative Name'
