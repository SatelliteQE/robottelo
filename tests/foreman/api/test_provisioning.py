"""Provisioning tests

:Requirement: Provisioning

:CaseAutomation: Automated

:CaseComponent: Provisioning

:Team: Rocket

:CaseImportance: Critical

"""

import re

from fauxfactory import gen_string
import pytest
from wait_for import TimedOutError, wait_for
from wrapanapi.systems.virtualcenter import VMWareVirtualMachine

from robottelo.config import settings
from robottelo.enums import NetworkType
from robottelo.logging import logger
from robottelo.utils.installer import InstallerCommand
from robottelo.utils.issue_handlers import is_open


def _read_log(ch, pattern):
    """Read the first line from the given channel buffer and return the matching line"""
    # read lines until the buffer is empty
    for log_line in ch.result.stdout.splitlines():
        logger.debug(f'foreman-tail: {log_line}')
        if re.search(pattern, log_line):
            return log_line
    else:
        return None


def _wait_for_log(channel, pattern, timeout=5, delay=0.2):
    """_read_log method enclosed in wait_for method"""
    matching_log = wait_for(
        _read_log,
        func_args=(
            channel,
            pattern,
        ),
        fail_condition=None,
        timeout=timeout,
        delay=delay,
        logger=logger,
    )
    return matching_log.out


def assert_host_logs(channel, pattern):
    """Reads foreman logs until given pattern found"""
    try:
        log = _wait_for_log(channel, pattern, timeout=300, delay=10)
        assert pattern in log
    except TimedOutError as err:
        raise AssertionError(f'Timed out waiting for {pattern} from VM') from err


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.on_premises_provisioning
@pytest.mark.ipv6_provisioning
@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
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
    configure_kea_dhcp6_server,
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

    :Verifies:SAT-20739,SAT-27869

    :customerscenario: true

    :parametrized: yes
    """
    if (
        pxe_loader.vm_firmware == 'bios'
        and module_provisioning_sat.sat.network_type == NetworkType.IPV6
    ):
        pytest.skip('Test cannot be run on BIOS as its not supported')
    host_mac_addr = provisioning_host.provisioning_nic_mac_addr
    sat = module_provisioning_sat.sat
    # Configure the grubx64.efi image to setup the interface and use TFTP to load the configuration
    if module_provisioning_sat.sat.network_type == NetworkType.IPV6:
        sat.execute("echo -e 'net_bootp6\nset root=tftp\nset prefix=(tftp)/grub2' > pre.cfg")
        sat.execute(
            'grub2-mkimage -c pre.cfg -o /var/lib/tftpboot/grub2/grubx64.efi -p /grub2/ -O x86_64-efi efinet efi_netfs efienv efifwsetup efi_gop tftp net normal chain configfile loadenv procfs romfs'
        )
    host = sat.api.Host(
        hostgroup=provisioning_hostgroup,
        organization=module_sca_manifest_org,
        location=module_location,
        name=gen_string('alpha').lower(),
        mac=host_mac_addr,
        operatingsystem=module_provisioning_rhel_content.os,
        host_parameters_attributes=[
            {'name': 'remote_execution_connect_by_ip', 'value': 'true', 'parameter_type': 'boolean'}
        ],
        build=True,  # put the host in build mode
    ).create(create_missing=False)
    # Clean up the host to free IP leases on Satellite.
    # broker should do that as a part of the teardown, putting here just to make sure.
    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))

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

    # The label checked above is generated dynamically and may not necessarily
    # represent the exact value that is stored in the database
    assert (
        len(sat.api.Host().search(query={'search': f'name="{host.name}" and build_status = built'}))
        == 1
    )

    # Change the hostname of the host as we know it already.
    # In the current infra environment we do not support
    # addressing hosts using FQDNs, falling back to IP.
    if is_open('SAT-30601') and module_provisioning_sat.sat.network_type == NetworkType.IPV4:
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
        assert expected_rhel_version in host_ssh_os.stdout, (
            'Different than the expected OS version was installed'
        )

        # Verify provisioning log exists on host at correct path
        assert provisioning_host.execute('test -s /root/install.post.log').status == 0
        assert provisioning_host.execute('test -s /mnt/sysimage/root/install.post.log').status == 1

        # Run a command on the host using REX to verify that Satellite's SSH key is present on the host
        # Add workaround for SAT-32007 and SAT-32006
        if is_open('SAT-32007') and is_open('SAT-32006'):
            assert (
                sat.execute('cat /dev/null > /usr/share/foreman-proxy/.ssh/known_hosts').status == 0
            )
        template_id = (
            sat.api.JobTemplate()
            .search(query={'search': 'name="Run Command - Script Default"'})[0]
            .id
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

        # check if katello-ca-consumer is not used while host registration
        assert provisioning_host.execute('rpm -qa |grep katello-ca-consumer').status == 1
        assert (
            'katello-ca-consumer'
            not in provisioning_host.execute('cat /root/install.post.log').stdout
        )
        # assert that the host is subscribed and consumes
        # subsctiption provided by the activation key
        assert provisioning_host.subscribed, 'Host is not subscribed'


@pytest.mark.e2e
@pytest.mark.upgrade
@pytest.mark.parametrize('pxe_loader', ['ipxe'], indirect=True)
@pytest.mark.on_premises_provisioning
@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
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
    host_mac_addr = provisioning_host.provisioning_nic_mac_addr
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
    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))

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
    assert expected_rhel_version in host_ssh_os.stdout, (
        f'The installed OS version differs from the expected version {expected_rhel_version}'
    )

    # Run a command on the host using REX to verify that Satellite's SSH key is present on the host
    # Add workaround for SAT-32007 and SAT-32006
    if is_open('SAT-32007') and is_open('SAT-32006'):
        assert sat.execute('cat /dev/null > /usr/share/foreman-proxy/.ssh/known_hosts').status == 0
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
@pytest.mark.upgrade
@pytest.mark.parametrize('pxe_loader', ['http_uefi'], indirect=True)
@pytest.mark.on_premises_provisioning
@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
def test_rhel_httpboot_provisioning(
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
    """Provision a host using httpboot workflow

    :id: 98c2865e-5d21-402e-ad01-c474b7fc4eee

    :steps:
        1. Configure satellite for provisioning
        2. provision a host using pxe loader as Grub2 UEFI HTTP
        3. Check that resulting host is registered to Satellite
        4. Check host is subscribed to Satellite

    :expectedresults:
        1. Provisioning via HTTP is successful
        2. Host installs right version of RHEL
        3. Satellite is able to run REX job on the host
        4. Host is registered to Satellite and subscription status is 'Success'

    :parametrized: yes

    :BlockedBy: SAT-20684

    :Verifies: SAT-20684
    """
    sat = module_provisioning_sat.sat
    # update grub2-efi package
    sat.cli.Packages.update(packages='grub2-efi', options={'assumeyes': True})
    host_mac_addr = provisioning_host.provisioning_nic_mac_addr
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
    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))

    # Start the VM, do not ensure that we can connect to SSHD
    provisioning_host.power_control(ensure=False)
    # check for proper HTTP requests
    shell = module_provisioning_sat.session.shell()
    shell.send('foreman-tail')
    shell.close()
    assert_host_logs(shell, f'GET /httpboot/grub2/grub.cfg-{host_mac_addr} with 200')
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
    assert expected_rhel_version in host_ssh_os.stdout, (
        f'The installed OS version differs from the expected version {expected_rhel_version}'
    )

    # Run a command on the host using REX to verify that Satellite's SSH key is present on the host
    # Add workaround for SAT-32007 and SAT-32006
    if is_open('SAT-32007') and is_open('SAT-32006'):
        assert sat.execute('cat /dev/null > /usr/share/foreman-proxy/.ssh/known_hosts').status == 0
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


@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.on_premises_provisioning
@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
def test_rhel_pxe_provisioning_fips_enabled(
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
    """Provision a host with host param fips_enabled set to true

    :id: 9e016e1d-757a-48e7-9159-131bb65dc4ef

    :steps:
        1. Configure satellite for provisioning
        2. Provision a host with host param fips_enabled
        3. Check that resulting host is registered to Satellite
        4. Check host is subscribed to Satellite

    :expectedresults:
        1. Provisioning with host param fips_enabled is successful
        2. Host installs right version of RHEL
        3. Satellite is able to run REX job on the fips_enabled host
        4. Host is registered to Satellite and subscription status is 'Success'

    :parametrized: yes

    :BZ: 2240076

    :Verifies: SAT-26071
    """
    sat = module_provisioning_sat.sat
    host_mac_addr = provisioning_host.provisioning_nic_mac_addr
    # Verify password hashing algorithm SHA512 is set in OS used for provisioning
    assert module_provisioning_rhel_content.os.password_hash == 'SHA512'

    host = sat.api.Host(
        hostgroup=provisioning_hostgroup,
        organization=module_sca_manifest_org,
        location=module_location,
        name=gen_string('alpha').lower(),
        mac=host_mac_addr,
        operatingsystem=module_provisioning_rhel_content.os,
        subnet=module_provisioning_sat.subnet,
        host_parameters_attributes=[
            {
                'name': 'remote_execution_connect_by_ip',
                'value': 'true',
                'parameter_type': 'boolean',
            },
            {'name': 'fips_enabled', 'value': 'true', 'parameter_type': 'boolean'},
        ],
        build=True,  # put the host in build mode
    ).create(create_missing=False)
    # Clean up the host to free IP leases on Satellite.
    # broker should do that as a part of the teardown, putting here just to make sure.
    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))
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
    assert expected_rhel_version in host_ssh_os.stdout, (
        f'The installed OS version differs from the expected version {expected_rhel_version}'
    )

    # Verify FIPS is enabled on host after provisioning is completed successfully
    result = provisioning_host.execute('cat /proc/sys/crypto/fips_enabled')
    assert (0 if is_open('SAT-20386') else 1) == int(result.stdout)

    # Run a command on the host using REX to verify that Satellite's SSH key is present on the host
    # Add workaround for SAT-32007 and SAT-32006
    if is_open('SAT-32007') and is_open('SAT-32006'):
        assert sat.execute('cat /dev/null > /usr/share/foreman-proxy/.ssh/known_hosts').status == 0
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
@pytest.mark.upgrade
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('pxe_loader', ['secureboot'], indirect=True)
@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
def test_rhel_pxe_provisioning_secureboot_enabled(
    request,
    module_provisioning_sat,
    vmwareclient,
    provisioning_vmware_host,
    pxe_loader,
    module_sca_manifest_org,
    module_location,
    module_provisioning_rhel_content,
    provisioning_hostgroup,
):
    """Simulate Secureboot baremetal provisioning of a RHEL system via PXE on vCenter provider

    :id: 8b33f545-c4a8-428d-8fd8-a5e402c8cd23

    :steps:
        1. Provision RHEL system via PXE on vCenter provider
        2. Check that resulting host is registered to Satellite
        3. Check host is subscribed to Satellite

    :expectedresults:
        1. Host installs right version of RHEL
        2. Host is registered to Satellite and subscription status is 'Success'
        3. Secureboot is enabled on the host

    :Verifies: SAT-25809

    :customerscenario: true

    :parametrized: yes
    """
    host_mac_addr = provisioning_vmware_host.provisioning_nic_mac_addr
    sat = module_provisioning_sat.sat
    host = sat.api.Host(
        hostgroup=provisioning_hostgroup,
        organization=module_sca_manifest_org,
        location=module_location,
        name=gen_string('alpha').lower(),
        mac=host_mac_addr,
        build=True,  # put the host in build mode
    ).create(create_missing=False)
    # Clean up the host to free IP leases on Satellite.
    # broker should do that as a part of the teardown, putting here just to make sure.
    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))

    # start the provisioning host on VMware, do not ensure that we can connect to SSHD
    vmware_host = VMWareVirtualMachine(vmwareclient, name=provisioning_vmware_host.name)
    vmware_host.start()

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
    provisioning_vmware_host.hostname = host.ip
    # Host is not blank anymore
    provisioning_vmware_host.blank = False

    # Wait for the host to be rebooted and SSH daemon to be started.
    provisioning_vmware_host.wait_for_connection()

    # Perform version check and check if root password is properly updated
    host_os = host.operatingsystem.read()
    expected_rhel_version = f'{host_os.major}.{host_os.minor}'

    if int(host_os.major) >= 9:
        assert (
            provisioning_vmware_host.execute(
                'echo -e "\nPermitRootLogin yes" >> /etc/ssh/sshd_config; systemctl restart sshd'
            ).status
            == 0
        )
    host_ssh_os = sat.execute(
        f'sshpass -p {settings.provisioning.host_root_password} '
        'ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no -o PasswordAuthentication=yes '
        f'-o UserKnownHostsFile=/dev/null root@{provisioning_vmware_host.hostname} cat /etc/redhat-release'
    )
    assert host_ssh_os.status == 0
    assert expected_rhel_version in host_ssh_os.stdout, (
        'Different than the expected OS version was installed'
    )

    # Verify host is subscribed and consumes subsctiption provided by the activation key
    assert provisioning_vmware_host.subscribed, 'Host is not subscribed'

    # Verify SecureBoot is enabled on host after provisioning is completed successfully
    assert 'SecureBoot enabled' in provisioning_vmware_host.execute('mokutil --sb-state').stdout


@pytest.mark.e2e
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
@pytest.mark.skip(reason='Skipping till we have destructive support')
@pytest.mark.on_premises_provisioning
@pytest.mark.rhel_ver_match(r'^(?!.*fips).*$')
def test_capsule_pxe_provisioning(
    request,
    capsule_provisioning_sat,
    module_capsule_configured,
    capsule_provisioning_rhel_content,
    module_sca_manifest_org,
    module_location,
    provisioning_host,
    pxe_loader,
    capsule_provisioning_hostgroup,
    module_lce_library,
    module_default_org_view,
    capsule_provisioning_lce_sync_setup,
):
    """Provision a host using external capsule

    :id: d76cd326-af4e-4bd5-b20c-128348e042d3

    :steps:
        1. Configure satellite and capsule for provisioning
        2. Provision a host using capsule as the content source
        3. Check that resulting host is registered to Satellite

    :expectedresults:
        1. Provisioning using external capsule is successful.
        1. Host installs right version of RHEL
        2. Satellite is able to run REX job on the host
        3. Host is registered to Satellite and subscription status is 'Success'

    :parametrized: yes
    """
    host_mac_addr = provisioning_host.provisioning_nic_mac_addr
    sat = capsule_provisioning_sat.sat
    cap = module_capsule_configured
    host = sat.api.Host(
        hostgroup=capsule_provisioning_hostgroup,
        organization=module_sca_manifest_org,
        location=module_location,
        content_facet_attributes={
            'content_view_id': capsule_provisioning_rhel_content.cv.id,
            'lifecycle_environment_id': module_lce_library.id,
        },
        name=gen_string('alpha').lower(),
        mac=host_mac_addr,
        operatingsystem=capsule_provisioning_rhel_content.os,
        subnet=capsule_provisioning_sat.subnet,
        host_parameters_attributes=[
            {
                'name': 'remote_execution_connect_by_ip',
                'value': 'true',
                'parameter_type': 'boolean',
            },
        ],
        build=True,  # put the host in build mode
    ).create(create_missing=False)
    # Clean up the host to free IP leases on Satellite.
    # broker should do that as a part of the teardown, putting here just to make sure.
    request.addfinalizer(lambda: sat.provisioning_cleanup(host.name))
    # Start the VM, do not ensure that we can connect to SSHD
    provisioning_host.power_control(ensure=False)
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
    assert expected_rhel_version in host_ssh_os.stdout, (
        f'The installed OS version differs from the expected version {expected_rhel_version}'
    )

    # Run a command on the host using REX to verify that Satellite's SSH key is present on the host
    # Add workaround for SAT-32007 and SAT-32006
    if is_open('SAT-32007') and is_open('SAT-32006'):
        assert sat.execute('cat /dev/null > /usr/share/foreman-proxy/.ssh/known_hosts').status == 0
    template_id = (
        sat.api.JobTemplate().search(query={'search': 'name="Run Command - Script Default"'})[0].id
    )
    job = sat.api.JobInvocation().run(
        data={
            'job_template_id': template_id,
            'inputs': {
                'command': f'subscription-manager config | grep "hostname = {cap.hostname}"'
            },
            'search_query': f"name = {host.name}",
            'targeting_type': 'static_query',
        },
    )
    assert job['result'] == 'success', 'Job invocation failed'

    # assert that the host is subscribed and consumes
    # subsctiption provided by the activation key
    assert provisioning_host.subscribed, 'Host is not subscribed'


@pytest.mark.stubbed
def test_rhel_provisioning_using_realm():
    """Provision a host using realm

    :id: 687e7d71-7e46-46d5-939b-4562f88c4598

    :steps:
        1. Configure satellite for provisioning
        2. Configure Satellite for Realm support
        3. Provision a Host
        4. Check host is subscribed to Satellite

    :expectedresults:
        1. Provisioning via Realm is successful
        2. Check if the provisioned host is automatically registered to IdM
        3. Host installs right version of RHEL
        4. Satellite is able to run REX job on the host
        5. Host is registered to Satellite and subscription status is 'Success'

    :CaseAutomation: NotAutomated
    """
