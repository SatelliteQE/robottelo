"""Tests for Infoblox Plugin

:Requirement: Infoblox, Installer

:CaseComponent: DHCPDNS

:Team: Rocket

:CaseImportance: High

"""

from fauxfactory import gen_mac, gen_string
import pytest
import requests
from requests.exceptions import HTTPError

from robottelo.config import settings
from robottelo.utils.installer import InstallerCommand

pytestmark = pytest.mark.destructive

dhcp_isc_package = 'rubygem-smart_proxy_dhcp_remote_isc'
infoblox_package = 'rubygem-infoblox'
infoblox_dhcp_package = 'rubygem-smart_proxy_dhcp_infoblox'
infoblox_dns_package = 'rubygem-smart_proxy_dns_infoblox'

params = [
    (
        'enable-foreman-proxy-plugin-dhcp-remote-isc',
        {'foreman-proxy-dhcp': 'true'},
        f'rpm -q {dhcp_isc_package}',
    ),
    (
        'enable-foreman-proxy-plugin-dhcp-infoblox',
        {
            'foreman-proxy-plugin-dhcp-infoblox-username': 'fakeusername',
            'foreman-proxy-plugin-dhcp-infoblox-password': 'fakepassword',
        },
        f'echo {infoblox_package} {infoblox_dhcp_package} | xargs rpm -q',
    ),
    (
        'enable-foreman-proxy-plugin-dns-infoblox',
        {
            'foreman-proxy-plugin-dns-infoblox-username': 'fakeusername',
            'foreman-proxy-plugin-dns-infoblox-password': 'fakepassword',
            'foreman-proxy-plugin-dns-infoblox-dns-server': 'infoblox.example.com',
        },
        f'echo {infoblox_package} {infoblox_dns_package} | xargs rpm -q',
    ),
]

infoblox_plugin_enable = [
    'enable-foreman-proxy-plugin-dhcp-infoblox',
    'enable-foreman-proxy-plugin-dns-infoblox',
]

infoblox_plugin_disable = [
    'no-enable-foreman-proxy-plugin-dhcp-infoblox',
    'no-enable-foreman-proxy-plugin-dns-infoblox',
    'reset-foreman-proxy-dhcp-provider',
    'reset-foreman-proxy-dns-provider',
]
infoblox_plugin_disable_opts = {
    'foreman-proxy-dhcp': 'false',
    'foreman-proxy-dns': 'false',
}

infoblox_plugin_opts = {
    'foreman-proxy-dhcp': 'true',
    'foreman-proxy-dhcp-managed': 'false',
    'foreman-proxy-dhcp-provider': 'infoblox',
    'foreman-proxy-dhcp-server': settings.infoblox.hostname,
    'foreman-proxy-plugin-dhcp-infoblox-dns-view': 'default',
    'foreman-proxy-plugin-dhcp-infoblox-network-view': 'default',
    'foreman-proxy-plugin-dhcp-infoblox-username': settings.infoblox.username,
    'foreman-proxy-plugin-dhcp-infoblox-password': settings.infoblox.password,
    'foreman-proxy-plugin-dhcp-infoblox-record-type': 'fixedaddress',
    'foreman-proxy-dns': 'true',
    'foreman-proxy-dns-provider': 'infoblox',
    'foreman-proxy-plugin-dns-infoblox-username': settings.infoblox.username,
    'foreman-proxy-plugin-dns-infoblox-password': settings.infoblox.password,
    'foreman-proxy-plugin-dns-infoblox-dns-server': settings.infoblox.hostname,
    'foreman-proxy-plugin-dns-infoblox-dns-view': 'default',
}


@pytest.mark.tier4
@pytest.mark.parametrize(
    ('command_args', 'command_opts', 'rpm_command'),
    params,
    ids=['isc_dhcp', 'infoblox_dhcp', 'infoblox_dns'],
)
def test_plugin_installation(target_sat, command_args, command_opts, rpm_command):
    """Check that external DNS and DHCP plugins install correctly

    :id: c75aa5f3-870a-4f4a-9d7a-0a871b47fd6f

    :steps: Run installer with mininum options required to install plugins

    :expectedresults: Plugins install successfully

    :CaseAutomation: Automated

    :customerscenario: true

    :BZ: 1994490, 2000237
    """
    target_sat.register_to_cdn()
    installer = target_sat.install(InstallerCommand(command_args, **command_opts))
    assert 'Success!' in installer.stdout
    assert target_sat.execute(rpm_command).status == 0


@pytest.mark.e2e
@pytest.mark.rhel_ver_match('[8]')
def test_infoblox_end_to_end(
    request,
    module_sync_kickstart_content,
    module_provisioning_capsule,
    module_target_sat,
    module_sca_manifest_org,
    module_location,
    module_default_org_view,
    module_lce_library,
    default_architecture,
    default_partitiontable,
):
    """Verify end to end infoblox plugin integration and host creation with
       Infoblox as DHCP and DNS provider

    :id: 0aebdf39-84ba-4182-9a17-6eb523f1695f

    :steps:
        1. Run installer to integrate Satellite and Infoblox.
        2. Assert if DHCP, DNS provider and server is properly set.
        3. Create a host with proper domain and subnet.
        4. Check if A record is created with host ip and hostname on Infoblox
        5. Delete the host, domain, subnet

    :expectedresults: Satellite and Infoblox are integrated properly with DHCP, DNS
                      provider and server.Also, A record is created for the host created.

    :BZ: 1813953, 2210256

    :customerscenario: true
    """
    enable_infoblox_plugin = InstallerCommand(
        installer_args=infoblox_plugin_enable,
        installer_opts=infoblox_plugin_opts,
    )
    result = module_target_sat.install(enable_infoblox_plugin)
    assert result.status == 0
    assert 'Success!' in result.stdout

    installer = module_target_sat.install(
        InstallerCommand(help='| grep enable-foreman-proxy-plugin-dhcp-infoblox')
    )
    assert 'default: true' in installer.stdout

    installer = module_target_sat.install(
        InstallerCommand(help='| grep enable-foreman-proxy-plugin-dns-infoblox')
    )
    assert 'default: true' in installer.stdout

    installer = module_target_sat.install(
        InstallerCommand(help='| grep foreman-proxy-dhcp-provider')
    )
    assert 'current: "infoblox"' in installer.stdout

    installer = module_target_sat.install(
        InstallerCommand(help='| grep foreman-proxy-dns-provider')
    )
    assert 'current: "infoblox"' in installer.stdout

    installer = module_target_sat.install(InstallerCommand(help='| grep foreman-proxy-dhcp-server'))
    assert f'current: "{settings.infoblox.hostname}"' in installer.stdout

    installer = module_target_sat.install(
        InstallerCommand(help='| grep foreman-proxy-plugin-dns-infoblox-dns-server')
    )
    assert f'current: "{settings.infoblox.hostname}"' in installer.stdout

    macaddress = gen_mac(multicast=False)
    # using the domain name as defined in Infoblox DNS
    domain = module_target_sat.api.Domain(
        name=settings.infoblox.domain,
        location=[module_location],
        dns=module_provisioning_capsule.id,
        organization=[module_sca_manifest_org],
    ).create()
    subnet = module_target_sat.api.Subnet(
        location=[module_location],
        organization=[module_sca_manifest_org],
        network=settings.infoblox.network,
        cidr=settings.infoblox.network_prefix,
        mask=settings.infoblox.netmask,
        from_=settings.infoblox.start_range,
        to=settings.infoblox.end_range,
        boot_mode='DHCP',
        ipam='DHCP',
        dhcp=module_provisioning_capsule.id,
        tftp=module_provisioning_capsule.id,
        dns=module_provisioning_capsule.id,
        discovery=module_provisioning_capsule.id,
        remote_execution_proxy=[module_provisioning_capsule.id],
        domain=[domain.id],
    ).create()
    host = module_target_sat.api.Host(
        organization=module_sca_manifest_org,
        location=module_location,
        name=gen_string('alpha').lower(),
        mac=macaddress,
        operatingsystem=module_sync_kickstart_content.os,
        architecture=default_architecture,
        domain=domain,
        subnet=subnet,
        root_pass=settings.provisioning.host_root_password,
        ptable=default_partitiontable,
        content_facet_attributes={
            'content_source_id': module_provisioning_capsule.id,
            'content_view_id': module_default_org_view.id,
            'lifecycle_environment_id': module_lce_library.id,
        },
    ).create()
    # check if A Record is created for the host IP on Infoblox
    url = f'https://{settings.infoblox.hostname}/wapi/v2.0/ipv4address?ip_address={host.ip}'
    auth = (settings.infoblox.username, settings.infoblox.password)
    result = requests.get(url, auth=auth, verify=False)
    assert result.status_code == 200
    # check hostname and ip is present in A record
    assert host.name in result.text
    assert host.ip in result.text
    # delete host
    module_target_sat.api.Subnet(id=subnet.id, domain=[]).update()
    module_target_sat.api.Host(id=host.id).delete()
    module_target_sat.api.Subnet(id=subnet.id).delete()
    module_target_sat.api.Domain(id=domain.id).delete()
    with pytest.raises(HTTPError):
        host.read()
    # disable dhcp and dns plugin
    disable_infoblox_plugin = InstallerCommand(
        installer_args=infoblox_plugin_disable, installer_opts=infoblox_plugin_disable_opts
    )
    result = module_target_sat.install(disable_infoblox_plugin)
    assert result.status == 0
    assert 'Success!' in result.stdout
    installer = module_target_sat.install(
        InstallerCommand(help='| grep enable-foreman-proxy-plugin-dhcp-infoblox')
    )
    assert 'default: false' in installer.stdout

    installer = module_target_sat.install(
        InstallerCommand(help='| grep enable-foreman-proxy-plugin-dns-infoblox')
    )
    assert 'default: false' in installer.stdout
