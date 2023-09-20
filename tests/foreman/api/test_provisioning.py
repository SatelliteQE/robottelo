"""Provisioning tests

:Requirement: Provisioning

:CaseAutomation: NotAutomated

:CaseLevel: System

:CaseComponent: Provisioning

:Team: Rocket

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import pytest
from fauxfactory import gen_string
from wait_for import wait_for

from robottelo.config import settings
from robottelo.utils.installer import InstallerCommand


@pytest.mark.e2e
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.on_premises_provisioning
@pytest.mark.rhel_ver_match('[^6]')
def test_rhel_pxe_provisioning(
    request,
    module_provisioning_sat,
    module_sca_manifest_org,
    module_location,
    provisioning_host,
    pxe_loader,
    module_provisioning_rhel_content,
    provisioning_hostgroup,
    module_lce_library,
    module_default_org_view,
):
    """Simulate baremetal provisioning of a RHEL system via PXE on RHV provider

    :id: 8b33f545-c4a8-428d-8fd8-a5e402c8cd10

    :steps:
        1. Provision RHEL system via PXE on RHV
        2. Check that resulting host is registered to Satellite
        3. Check host is subscribed to Satellite

    :expectedresults:
        1. Host installs right version of RHEL
        2. Satellite is able to run REX job on the host
        3. Host is registered to Satellite and subscription status is 'Success'

    :BZ: 2105441, 1955861, 1784012

    :customerscenario: true

    :parametrized: yes
    """
    host_mac_addr = provisioning_host._broker_args['provisioning_nic_mac_addr']
    sat = module_provisioning_sat.sat
    host = sat.api.Host(
        hostgroup=provisioning_hostgroup,
        organization=module_sca_manifest_org,
        location=module_location,
        name=gen_string('alpha').lower(),
        mac=host_mac_addr,
        operatingsystem=module_provisioning_rhel_content.os,
        subnet=module_provisioning_sat.subnet,
        host_parameters_attributes=[
            {'name': 'remote_execution_connect_by_ip', 'value': 'true', 'parameter_type': 'boolean'}
        ],
        build=True,  # put the host in build mode
    ).create(create_missing=False)
    # Clean up the host to free IP leases on Satellite.
    # broker should do that as a part of the teardown, putting here just to make sure.
    request.addfinalizer(host.delete)
    # Start the VM, do not ensure that we can connect to SSHD
    provisioning_host.power_control(ensure=False)

    # TODO: Implement Satellite log capturing logic to verify that
    # all the events are captured in the logs.

    # Host should do call back to the Satellite reporting
    # the result of the installation. Wait until Satellite reports that the host is installed.
    wait_for(
        lambda: host.read().build_status_label != 'Pending installation',
        timeout=1500,
        delay=10,
    )
    host = host.read()
    assert host.build_status_label == 'Installed'

    # Change the hostname of the host as we know it already.
    # In the current infra environment we do not support
    # addressing hosts using FQDNs, falling back to IP.
    provisioning_host.hostname = host.ip
    # Host is not blank anymore
    provisioning_host.blank = False

    # Wait for the host to be rebooted and SSH daemon to be started.
    provisioning_host.wait_for_connection()

    # Perform version check and check if root password is properly updated
    host_os = host.operatingsystem.read()
    expected_rhel_version = f'{host_os.major}.{host_os.minor}'

    if int(host_os.major) >= 9:
        assert (
            provisioning_host.execute(
                'echo -e "\nPermitRootLogin yes" >> /etc/ssh/sshd_config; systemctl restart sshd'
            ).status
            == 0
        )
    host_ssh_os = sat.execute(
        f'sshpass -p {settings.provisioning.host_root_password} '
        'ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no -o PasswordAuthentication=yes '
        f'-o UserKnownHostsFile=/dev/null root@{provisioning_host.hostname} cat /etc/redhat-release'
    )
    assert host_ssh_os.status == 0
    assert (
        expected_rhel_version in host_ssh_os.stdout
    ), 'Different than the expected OS version was installed'

    # Verify provisioning log exists on host at correct path
    assert provisioning_host.execute('test -s /root/install.post.log').status == 0
    assert provisioning_host.execute('test -s /mnt/sysimage/root/install.post.log').status == 1

    # Run a command on the host using REX to verify that Satellite's SSH key is present on the host
    template_id = (
        sat.api.JobTemplate().search(query={'search': 'name="Run Command - Script Default"'})[0].id
    )
    job = sat.api.JobInvocation().run(
        data={
            'job_template_id': template_id,
            'inputs': {
                'command': f'subscription-manager config | grep "hostname = {sat.hostname}"'
            },
            'search_query': f"name = {host.name}",
            'targeting_type': 'static_query',
        },
    )
    assert job['result'] == 'success', 'Job invocation failed'

    # assert that the host is subscribed and consumes
    # subsctiption provided by the activation key
    assert provisioning_host.subscribed, 'Host is not subscribed'


@pytest.mark.e2e
@pytest.mark.parametrize('pxe_loader', ['ipxe'], indirect=True)
@pytest.mark.on_premises_provisioning
@pytest.mark.rhel_ver_match('[^6]')
def test_rhel_ipxe_provisioning(
    request,
    module_provisioning_sat,
    module_sca_manifest_org,
    module_location,
    provisioning_host,
    pxe_loader,
    module_provisioning_rhel_content,
    provisioning_hostgroup,
    module_lce_library,
    module_default_org_view,
):
    """Provision a host using iPXE workflow

    :id: 9e016e1d-757a-48e7-9159-131bb65dc4ed

    :steps:
        1. Configure satellite for provisioning
        2. provision a host
        3. Check that resulting host is registered to Satellite
        4. Check host is subscribed to Satellite

    :expectedresults:
        1. Provisioning via iPXE is successful
        2. Host installs right version of RHEL
        3. Satellite is able to run REX job on the host
        4. Host is registered to Satellite and subscription status is 'Success'

    :parametrized: yes
    """
    # TODO: parametrize iPXE Chain BIOS as pxe loader after #BZ:2171172 is fixed
    sat = module_provisioning_sat.sat
    # set http url
    ipxe_http_url = sat.install(
        InstallerCommand(
            f'foreman-proxy-dhcp-ipxefilename "http://{sat.hostname}/unattended/iPXE?bootstrap=1"'
        )
    )
    assert ipxe_http_url.status == 0
    host_mac_addr = provisioning_host._broker_args['provisioning_nic_mac_addr']
    host = sat.api.Host(
        hostgroup=provisioning_hostgroup,
        organization=module_sca_manifest_org,
        location=module_location,
        name=gen_string('alpha').lower(),
        mac=host_mac_addr,
        operatingsystem=module_provisioning_rhel_content.os,
        subnet=module_provisioning_sat.subnet,
        host_parameters_attributes=[
            {'name': 'remote_execution_connect_by_ip', 'value': 'true', 'parameter_type': 'boolean'}
        ],
        build=True,  # put the host in build mode
    ).create(create_missing=False)
    # Clean up the host to free IP leases on Satellite.
    # broker should do that as a part of the teardown, putting here just to make sure.
    request.addfinalizer(host.delete)
    # Start the VM, do not ensure that we can connect to SSHD
    provisioning_host.power_control(ensure=False)

    # TODO: Implement Satellite log capturing logic to verify that
    # all the events are captured in the logs.

    # Host should do call back to the Satellite reporting
    # the result of the installation. Wait until Satellite reports that the host is installed.
    wait_for(
        lambda: host.read().build_status_label != 'Pending installation',
        timeout=1500,
        delay=10,
    )
    host = host.read()
    assert host.build_status_label == 'Installed'

    # Change the hostname of the host as we know it already.
    # In the current infra environment we do not support
    # addressing hosts using FQDNs, falling back to IP.
    provisioning_host.hostname = host.ip
    # Host is not blank anymore
    provisioning_host.blank = False

    # Wait for the host to be rebooted and SSH daemon to be started.
    provisioning_host.wait_for_connection()

    # Perform version check and check if root password is properly updated
    host_os = host.operatingsystem.read()
    expected_rhel_version = f'{host_os.major}.{host_os.minor}'

    if int(host_os.major) >= 9:
        assert (
            provisioning_host.execute(
                'echo -e "\nPermitRootLogin yes" >> /etc/ssh/sshd_config; systemctl restart sshd'
            ).status
            == 0
        )
    host_ssh_os = sat.execute(
        f'sshpass -p {settings.provisioning.host_root_password} '
        'ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no -o PasswordAuthentication=yes '
        f'-o UserKnownHostsFile=/dev/null root@{provisioning_host.hostname} cat /etc/redhat-release'
    )
    assert host_ssh_os.status == 0
    assert (
        expected_rhel_version in host_ssh_os.stdout
    ), f'The installed OS version differs from the expected version {expected_rhel_version}'

    # Run a command on the host using REX to verify that Satellite's SSH key is present on the host
    template_id = (
        sat.api.JobTemplate().search(query={'search': 'name="Run Command - Script Default"'})[0].id
    )
    job = sat.api.JobInvocation().run(
        data={
            'job_template_id': template_id,
            'inputs': {
                'command': f'subscription-manager config | grep "hostname = {sat.hostname}"'
            },
            'search_query': f"name = {host.name}",
            'targeting_type': 'static_query',
        },
    )
    assert job['result'] == 'success', 'Job invocation failed'

    # assert that the host is subscribed and consumes
    # subsctiption provided by the activation key
    assert provisioning_host.subscribed, 'Host is not subscribed'
