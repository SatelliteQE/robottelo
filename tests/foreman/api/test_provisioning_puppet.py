"""Test class for puppet plugin CLI

:Requirement: Puppet

:CaseAutomation: Automated

:CaseLevel: Acceptance

:CaseComponent: Puppet

:Team: Rocket

:TestType: Functional

:CaseImportance: Medium

:Upstream: No
"""
import pytest
import requests
from fauxfactory import gen_string
from packaging.version import Version
from wait_for import wait_for


@pytest.mark.e2e
def test_positive_puppet_bootstrap(
    session_puppet_enabled_sat,
    session_puppet_enabled_proxy,
    session_puppet_default_os,
    module_puppet_org,
    module_puppet_environment,
):
    """Test that provisioning template renders snippet for puppet bootstrapping.

    :id: 71140e1a-6e4d-4110-bb2d-8d381f183d64

    :setup:
        1. Requires Satellite with http and templates feature enabled.

    :steps:
        1. Create a host providing puppet env, proxy and params.
        2. Get rendered provisioning template using host's token.
        3. Check the render contains puppet snippet in it.

    :expectedresults:
        1. Puppet snippet rendered in the provisioning template.
    """
    host_params = [
        {
            'name': 'enable-puppet7',
            'value': 'True',
            'parameter-type': 'boolean',
        }
    ]

    host = session_puppet_enabled_sat.api.Host(
        build=True,
        environment=module_puppet_environment,
        host_parameters_attributes=host_params,
        organization=module_puppet_org,
        operatingsystem=session_puppet_default_os,
        puppet_proxy=session_puppet_enabled_proxy,
        puppet_ca_proxy=session_puppet_enabled_proxy,
        root_pass=gen_string('alphanumeric'),
    ).create()

    render = requests.get(
        (
            f'http://{session_puppet_enabled_sat.hostname}:8000/'
            f'unattended/provision?token={host.token}'
        ),
    ).text

    puppet_config = (
        "if [ -f /usr/bin/dnf ]; then\n"
        "  dnf -y install puppet-agent\n"
        "else\n"
        "  yum -t -y install puppet-agent\n"
        "fi\n"
        "\n"
        "cat > /etc/puppetlabs/puppet/puppet.conf << EOF\n"
        "[main]\n"
        "\n"
        "[agent]\n"
        "pluginsync      = true\n"
        "report          = true\n"
        f"ca_server       = {session_puppet_enabled_proxy.name}\n"
        f"certname        = {host.name}\n"
        f"server          = {session_puppet_enabled_proxy.name}\n"
        f"environment     = {module_puppet_environment.name}\n"
    )
    puppet_run = (
        'puppet agent --config /etc/puppetlabs/puppet/puppet.conf --onetime '
        f'--tags no_such_tag --server {session_puppet_enabled_proxy.name}'
    )

    assert puppet_config in render
    assert puppet_run in render


@pytest.mark.on_premises_provisioning
@pytest.mark.rhel_ver_match('[^6]')
def test_host_provisioning_with_external_puppetserver(
    request,
    external_puppet_server,
    module_provisioning_sat,
    module_sca_manifest_org,
    module_location,
    provisioning_host,
    module_provisioning_rhel_content,
    provisioning_hostgroup,
    module_lce_library,
    module_default_org_view,
):
    """Baremetal provisioning of a RHEL system via PXE with external puppetserver host params

    :id: b036807a-bd44-11ed-b57d-e7f6b735234b

    :steps:
        1. Provision RHEL system via PXE with host params puppet_server and puppet_ca_server
            set as external puppetserver hostname
        2. Check that resulting host is registered to Satellite,
            and puppet-agent package is installed
        3. Check puppet config for server and ca_server under agent section
        4. Run puppet and check installed module template in /etc/motd

    :expectedresults:
        1. Host installs the correct version of RHEL
        2. Host is registered to Satellite and puppet-agent is installed from client repo
        3. Puppet config points to external puppetserver
            for server and ca_server under agent section
        4. /etc/motd contains content of theforeman/motd puppet module

    :BZ: 2106475, 2174734

    :customerscenario: true
    """
    puppet_env = 'production'
    host_mac_addr = provisioning_host._broker_args['provisioning_nic_mac_addr']
    sat = module_provisioning_sat.sat
    host = sat.api.Host(
        hostgroup=provisioning_hostgroup,
        organization=module_sca_manifest_org,
        location=module_location,
        content_facet_attributes={
            'content_view_id': module_provisioning_rhel_content.cv.id,
            'lifecycle_environment_id': module_lce_library.id,
        },
        name=gen_string('alpha').lower(),
        mac=host_mac_addr,
        operatingsystem=module_provisioning_rhel_content.os,
        subnet=module_provisioning_sat.subnet,
        host_parameters_attributes=[
            {'name': 'puppet_server', 'value': f'{external_puppet_server.hostname}'},
            {'name': 'puppet_ca_server', 'value': f'{external_puppet_server.hostname}'},
            {'name': 'puppet_environment', 'value': f'{puppet_env}'},
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
        raise ConnectionRefusedError('Timed out waiting for SSH daemon to start on the host')

    # Perform version check
    host_os = host.operatingsystem.read()
    expected_rhel_version = Version(f'{host_os.major}.{host_os.minor}')
    assert (
        provisioning_host.os_version == expected_rhel_version
    ), 'Different than the expected OS version was installed'

    # assert that the host is subscribed and consumes subsctiption provided by the activation key
    assert provisioning_host.subscribed, 'Host is not subscribed'

    # Validate external Puppet server deployment with Satellite
    assert (
        provisioning_host.execute('rpm -q puppet-agent').status == 0
    ), 'Puppet agent package is not installed'

    assert (
        external_puppet_server.hostname
        in provisioning_host.execute('puppet config print server --section agent').stdout
    )
    assert (
        external_puppet_server.hostname
        in provisioning_host.execute('puppet config print ca_server --section agent').stdout
    )
    assert (
        host.name
        in provisioning_host.execute('puppet config print certname --section agent').stdout
    )
    assert (
        puppet_env
        in provisioning_host.execute('puppet config print environment --section agent').stdout
    )

    # Run puppet-agent which fails as certs aren't signed
    provisioning_host.execute('/opt/puppetlabs/bin/puppet agent -t')
    # Sign certs on Puppet server for the provisioned host
    external_puppet_server.execute(f'puppetserver ca sign --certname {host.name}')
    # Run puppet-agent again, validate rc and stdout
    result = provisioning_host.execute('/opt/puppetlabs/bin/puppet agent -t')
    assert 'Applied catalog' in result.stdout
    # 0 if run succeds, 2 if run succeeds and some resources changed
    assert result.status in [0, 2]

    # Check /etc/motd contains contents from theforeman/motd module
    assert (
        'virtual machine that is the property of the Foreman project'
        in provisioning_host.execute('cat /etc/motd').stdout
    )
