# katello_certs_check Fixtures
from pathlib import Path

import pytest
from broker import Broker
from fauxfactory import gen_string

from robottelo.constants import CERT_DATA as cert_data
from robottelo.hosts import Capsule
from robottelo.hosts import ContentHost


@pytest.fixture
def certs_vm_setup(request):
    """Create VM and register content host"""
    target_cores = request.param.get('target_cores', 1)
    target_memory = request.param.get('target_memory', '1GiB')
    with Broker(
        nick=request.param['nick'],
        host_classes={'host': ContentHost},
        target_cores=target_cores,
        target_memory=target_memory,
    ) as host:
        cert_data['key_file_name'] = f'{host.hostname}/{host.hostname}.key'
        cert_data['cert_file_name'] = f'{host.hostname}/{host.hostname}.crt'
        host.custom_cert_generate(cert_data['capsule_hostname'])
        yield cert_data, host


@pytest.fixture
def cert_setup_destructive_teardown(target_sat):
    """Get host name, scripts, and create working directory."""
    cert_data['key_file_name'] = f'{target_sat.hostname}/{target_sat.hostname}.key'
    cert_data['cert_file_name'] = f'{target_sat.hostname}/{target_sat.hostname}.crt'
    target_sat.custom_cert_generate(cert_data['capsule_hostname'])
    yield cert_data, target_sat
    target_sat.custom_certs_cleanup()


@pytest.fixture
def capsule_certs_teardown(target_sat):
    """Create working directory and file."""
    capsule = Capsule('capsule.example.com')
    tmp_dir = f"/var/tmp/{gen_string('alpha', 6)}"
    caps_cert_file = f'{tmp_dir}/ssl-build/capsule.example.com/cert-data'
    # Use same path locally as on remote for storing files
    Path(f'{tmp_dir}/ssl-build/capsule.example.com/').mkdir(parents=True, exist_ok=True)
    assert target_sat.execute(f'mkdir {tmp_dir}').status == 0, 'Create working dir failed.'
    # Generate a Capsule cert for capsule.example.com
    target_sat.capsule_certs_generate(capsule, f'{tmp_dir}/capsule_certs.tar')
    return {
        'tmp_dir': tmp_dir,
        'caps_cert_file': caps_cert_file,
        'capsule_hostname': capsule.hostname,
    }, target_sat


@pytest.fixture(scope='module')
def cert_setup_teardown(module_target_sat):
    """Get host name, scripts, and create working directory."""
    cert_data['key_file_name'] = f'{module_target_sat.hostname}/{module_target_sat.hostname}.key'
    cert_data['cert_file_name'] = f'{module_target_sat.hostname}/{module_target_sat.hostname}.crt'
    module_target_sat.custom_cert_generate(cert_data['capsule_hostname'])
    yield cert_data, module_target_sat
    module_target_sat.custom_certs_cleanup()
