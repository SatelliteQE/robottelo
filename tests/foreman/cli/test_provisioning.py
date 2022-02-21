"""Provisioning tests

:Requirement: Provisioning

:CaseAutomation: NotAutomated

:CaseLevel: System

:CaseComponent: Provisioning

:Assignee: sganar

:TestType: Functional

:CaseImportance: Critical

:Upstream: No
"""
import ipaddress
import re

import pytest
from broker.broker import VMBroker
from fauxfactory import gen_string
from box import Box

from robottelo import constants
from robottelo.config import settings
from robottelo.api.utils import enable_rhrepo_and_fetchid


# TODO: parametrize this fixture to give more than one RHEL
@pytest.fixture(scope="module")
def provisioning_rhel_content(default_sat, module_manifest_org):
    sat = default_sat
    repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=module_manifest_org.id,
        product=constants.PRDS['rhel8'],
        repo=constants.REPOS['rhel8_bos_ks']['name'],
        reposet=constants.REPOSET['rhel8_bos_ks'],
        releasever='8.4',  # should be parametrizable - from fixture

    ) # TODO: add appstream repo
    repo = sat.api.Repository(id=repo_id).read()
    repo.sync()
    repo = repo.read()

    os = (
        sat.api.OperatingSystem()
        .search(query={'search': 'family=Redhat and major=8 and minor=4'})[0]  # parametrize fixture
        .read()
    )
    return Box({"sat": sat, "os": os, "repo": repo})

@pytest.fixture(scope='module')
def provisioning_sat(
    default_sat,
    provisioning_rhel_content,
    module_manifest_org,
    module_location,
    default_architecture,
    default_partitiontable,
):
    sat = default_sat
    host_root_pass = settings.provisioning.host_root_password
    pxe_loader = "PXELinux BIOS"  # TODO: this should come from fixture
    provisioning_domain_name = f"{gen_string('alpha').lower()}.foo"
    provisioning_activation_key = f"satellite-{settings.robottelo.satellite_version}-qa-rhel{sat.os_version.major}"
    provisioning_network_vlan_id = settings.provisioning.vlan_id

    provisioning_network = None
    provisioning_network_addr = None
    provisioning_gw_ipv4 = None

    # provisioning_network = "10.1.5.88/29"  # to be supplied by broker's output
    # provisioning_gw_ipv4 = "10.1.5.94"  # to be supplied by broker's output
    # provisioning_interface = "eth1"  # to be supplied by broker's output

    # provisioning_network = ipaddress.IPv4Network(provisioning_network)  # to be supplied by broker's output
    # provisioning_network_addr = str(provisioning_network.network_address)  # to be supplied by broker's output

    # provisioning_addr_ipv4 = str(list(provisioning_network.hosts())[0])  # to be supplied by broker's output
    # provisioning_addr_ipv4 = f"{provisioning_addr_ipv4}/{provisioning_network.prefixlen}"  # to be supplied by broker's output

    # range = subnet host range - GW address - Satellite host address
    provisioning_dhcp_host_range = list(provisioning_network.hosts())[1:-1]
    provisioning_network_netmask = str(provisioning_network.netmask)
    provisioning_upstream_dns = []
    resolv_conf = sat.execute("grep nameserver /etc/resolv.conf").stdout.splitlines()
    for line in resolv_conf:
        match = re.search(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", line)
        if match:
            provisioning_upstream_dns.append(match.group())  # TODO: make a nice log message if no nameserver was found
    provisioning_upstream_dns.reverse()  # TODO: use reverse record?
    provisioning_upstream_dns_primary = (
        provisioning_upstream_dns.pop()
    )  # There should always be at least one upstream DNS
    provisioning_upstream_dns_secondary = (
        provisioning_upstream_dns.pop() if len(provisioning_upstream_dns) else None
    )
    
    # run add-configure-vlan-interface on the Satellite host
    VMBroker().execute(
        workflow="add-configure-vlan-iface",
        target_vlan_id=provisioning_network_vlan_id,
        target_host=sat.name,
    )

    # run configure-provisioning-ifaces-rhv on Satellite host
    # TODO: JT should accept variables like and do not assume them
    VMBroker().execute(
        job_template="configure-provisioning-ifaces-rhv",
        provisioning_dns_zone=provisioning_domain_name,
        activation_key=provisioning_activation_key,
        target_host=sat.name,
    )

    # use internal Capsule
    provisioning_capsule = sat.api.SmartProxy().search(
        query={'search': f'name={sat.hostname}'}
    )[0].read()
    
    domain = sat.api.Domain(
        location=[module_location],
        organization=[module_manifest_org],
        dns=provisioning_capsule.id,
        name=provisioning_domain_name,
    ).create()

    subnet = sat.api.Subnet(
        location=[module_location],
        organization=[module_manifest_org],
        network=provisioning_network_addr,
        mask=provisioning_network_netmask,
        gateway=provisioning_gw_ipv4,
        from_=str(provisioning_dhcp_host_range[:1][0]),
        to=str(provisioning_dhcp_host_range[-1:][0]),
        dns_primary=provisioning_upstream_dns_primary,
        dns_secondary=provisioning_upstream_dns_secondary,
        boot_mode="DHCP",
        dhcp=provisioning_capsule.id,
        tftp=provisioning_capsule.id,
        template=provisioning_capsule.id,
        dns=provisioning_capsule.id,
        httpboot=provisioning_capsule.id,
        discovery=provisioning_capsule.id,
        remote_execution_proxy=[provisioning_capsule.id],
        domain=[domain.id],  # TODO: add IPAM param
    ).create()

    # use default Environment
    lce = (
        sat.api.LifecycleEnvironment(organization=module_manifest_org)
        .search(query={'search': f'name={constants.ENVIRONMENT}'})[0]
        .read()
    )

    # use default Content View
    cv = (
        sat.api.ContentView(
            organization=module_manifest_org,
            name=constants.DEFAULT_CV,
        )
        .search()[0]
        .read()
    )

    hostgroup = sat.api.HostGroup(
        organization=[module_manifest_org],
        location=[module_location],
        architecture=default_architecture,
        domain=domain,
        content_source=provisioning_capsule.id,
        content_view=cv,
        kickstart_repository=provisioning_rhel_content.repo,
        lifecycle_environment=lce,
        root_pass=host_root_pass,
        operatingsystem=provisioning_rhel_content.os,
        ptable=default_partitiontable,
        subnet=subnet,
        pxe_loader=pxe_loader,
    ).create()

    return Box({"sat": sat, "hostgroup": hostgroup, "subnet": subnet, "cv": cv, "lce": lce})


@pytest.fixture(scope="module")
def provisioning_contenthost(rhel8_contenthost):
    provisioning_network_vlan_id = settings.provisioning.vlan_id
    provisioning_vm_firmware = "bios"

    # run add-configure-vlan-interface on the host-to-be-provisioned
    VMBroker().execute(
        workflow="add-configure-vlan-iface",
        target_vlan_id=provisioning_network_vlan_id,
        target_host=rhel8_contenthost.name,
    )

    # run configure-pxe-boot-rhv on the host-to-be-provisioned
    VMBroker().execute(
        job_template="configure-pxe-boot-rhv",
        target_host=rhel8_contenthost.name,
        target_vlan_id=provisioning_network_vlan_id,
        target_vm_firmware=provisioning_vm_firmware,
    )

    ######## begin mock ########
    from robottelo.hosts import ContentHost
    rhel8_contenthost = ContentHost(hostname="dhcp-2-235.vms.sat.rdu2.redhat.com", username="root", password="dog8code")
    ######## end mock ########

    contenthost_mac_addr = rhel8_contenthost.execute("cat /sys/class/net/eth1/address").stdout.splitlines()[0]
    return Box({"mac_addr": contenthost_mac_addr})


@pytest.mark.stubbed
@pytest.mark.on_premises_provisioning
@pytest.mark.tier3
def test_rhel_pxe_provisioning_on_libvirt():
    """Provision RHEL system via PXE on libvirt and make sure it behaves

    :id: a272a594-f758-40ef-95ec-813245e44b63

    :steps:
        1. Provision RHEL system via PXE on libvirt
        2. Check that resulting host is registered to Satellite
        3. Check host can install package from Satellite

    :expectedresults:
        1. Host installs
        2. Host is registered to Satellite and subscription status is 'Success'
        3. Host can install package from Satellite
    """


# @pytest.mark.on_premises_provisioning
def test_rhel_pxe_provisioning_on_rhv(
    provisioning_sat,
    module_manifest_org,
    module_location,
    provisioning_contenthost,
    provisioning_rhel_content,
):
    """Provision RHEL system via PXE on RHV and make sure it behaves

    :id: 798b8d0e-e2c8-4860-a3f0-4f99ea0529bf

    :steps:
        1. Provision RHEL system via PXE on RHV
        2. Check that resulting host is registered to Satellite
        3. Check host can install package from Satellite

    :expectedresults:
        1. Host installs
        2. Host is registered to Satellite and subscription status is 'Success'
        3. Host can install package from Satellite
    """
    sat = provisioning_sat.sat
    contenthost_mac_addr = provisioning_contenthost.mac_addr
    hostgroup = provisioning_sat.hostgroup
    subnet = provisioning_sat.subnet
    os = provisioning_rhel_content.os
    cv = provisioning_sat.cv
    lce = provisioning_sat.lce

    host = provisioning_sat.api.Host(
        hostgroup=hostgroup,
        organization=module_manifest_org,
        location=module_location,
        content_facet_attributes={'content_view_id': cv.id, 'lifecycle_environment_id': lce.id},
        name=gen_string('alpha'),
        mac=contenthost_mac_addr,
        operatingsystem=os,
        subnet=subnet,
        # ip="10.1.5.91"
    ).create(create_missing=False)
