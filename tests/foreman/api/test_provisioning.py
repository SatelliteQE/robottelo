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
from packaging.version import Version
from wait_for import wait_for


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
    """
    host_mac_addr = provisioning_host._broker_args['provisioning_nic_mac_addr']
    sat = module_provisioning_sat.sat

    host = sat.api.Host(
        hostgroup=provisioning_hostgroup,
        organization=module_sca_manifest_org,
        location=module_location,
        content_facet_attributes={
            'content_view_id': module_default_org_view.id,
            'lifecycle_environment_id': module_lce_library.id,
        },
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
    try:
        wait_for(
            provisioning_host.connect,
            fail_condition=lambda res: res is not None,
            handle_exception=True,
            raise_original=True,
            timeout=180,
            delay=1,
        )
    except ConnectionRefusedError:
        raise ConnectionRefusedError("Timed out waiting for SSH daemon to start on the host")

    # Perform version check
    host_os = host.operatingsystem.read()
    expected_rhel_version = Version(f'{host_os.major}.{host_os.minor}')
    assert (
        provisioning_host.os_version == expected_rhel_version
    ), 'Different than the expected OS version was installed'

    # Run a command on the host using REX to verify that Satellite's SSH key is present on the host
    template_id = (
        sat.api.JobTemplate().search(query={'search': 'name="Run Command - Script Default"'})[0].id
    )
    job = sat.api.JobInvocation().run(
        data={
            'job_template_id': template_id,
            'inputs': {
                'command': f'grep KATELLO_SERVER={sat.hostname} /usr/bin/katello-rhsm-consumer'
            },
            'search_query': f"name = {host.name}",
            'targeting_type': 'static_query',
        },
    )
    assert job['result'] == 'success', 'Job invocation failed'

    # assert that the host is subscribed and consumes
    # subsctiption provided by the activation key
    assert provisioning_host.subscribed, 'Host is not subscribed'
