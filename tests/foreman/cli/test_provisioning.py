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

from robottelo import constants
from robottelo.api.utils import enable_rhrepo_and_fetchid


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
@pytest.mark.tier3
def test_rhel_pxe_provisioning_on_rhv(
    default_sat,
    module_manifest_org,
    module_location,
    default_architecture,
    default_partitiontable,
    rhel7_contenthost,
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
    # to be set in settings
    # set vars names with ipv4?
    provisioning_domain_name = f"{gen_string('alpha').lower()}.foo"
    provisioning_network = "10.1.5.88/29"
    provisioning_gw_ipv4 = "10.1.5.94"
    provisioning_network_vlan_id = "1026"
    provisioning_interface = "eth1"
    provisioning_pxeloader = "pxe"  # rename to firmware
    provisioning_activation_key = "satellite-6.10-qa-rhel7" # add host_rhel_major, host_rhel_minor, architecture?, boot_mode="DHCP", root_pass, pxe_loader="PXELinux BIOS"
    # end of settings

    provisioning_network = ipaddress.IPv4Network(provisioning_network)
    provisioning_network_addr = str(provisioning_network.network_address)
    # let Satellite be the first one in the host range
    provisioning_addr_ipv4 = str(list(provisioning_network.hosts())[0])
    # TODO: rework JT to receive it in a different way
    provisioning_addr_ipv4 = f"{provisioning_addr_ipv4}/{provisioning_network.prefixlen}"
    # range = subnet host range - GW address - Satellite host address
    provisioning_dhcp_host_range = list(provisioning_network.hosts())[1:-1]
    provisioning_network_netmask = str(provisioning_network.netmask)
    provisioning_upstream_dns = []
    resolv_conf = default_sat.execute("grep nameserver /etc/resolv.conf").stdout.splitlines()
    for line in resolv_conf:
        match = re.search(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", line)
        if match:
            provisioning_upstream_dns.append(match.group())  # make a nice log message if no nameserver was found
    provisioning_upstream_dns.reverse()
    provisioning_upstream_dns_primary = (
        provisioning_upstream_dns.pop()
    )  # There should be always at least one upstream DNS
    provisioning_upstream_dns_secondary = (
        provisioning_upstream_dns.pop() if len(provisioning_upstream_dns) else None
    )

    # run add-configure-vlan-interface on the Satellite host
    VMBroker.execute(
        workflow="add-configure-vlan-iface",
        target_vlan_id=provisioning_network_vlan_id,
        target_host=default_sat.name,
    )

    # run configure-provisioning-ifaces-rhv on Satellite host
    # TODO: JT should accept variables like from_ip, to_ip and do not assume them
    VMBroker.execute(
        job_template="configure-provisioning-ifaces-rhv",
        provisioning_dns_zone=provisioning_domain_name,
        provisioning_iface=provisioning_interface,
        activation_key=provisioning_activation_key,
        provisioning_addr_ipv4=provisioning_addr_ipv4,
        provisioning_gw_ipv4=provisioning_gw_ipv4,
        target_host=default_sat.name,
    )

    provisioning_capsule = default_sat.api.SmartProxy().search(
        query={'search': f'name={default_sat.hostname}'}
    )[0].read()
    
    domain = default_sat.api.Domain(
        location=[module_location],
        organization=[module_manifest_org],
        dns=provisioning_capsule.id,
        name=provisioning_domain_name,
    ).create()

    subnet = default_sat.api.Subnet(
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
        httpboot=provisioning_capsule.id,  # not in nailgun master yet
        discovery=provisioning_capsule.id,
        remote_execution_proxy=[provisioning_capsule.id],
        domain=[domain.id],  # TODO: add IPAM param
    ).create()

    repo_id = enable_rhrepo_and_fetchid(
        basearch='x86_64',
        org_id=module_manifest_org.id,
        product=constants.PRDS['rhel8'],
        repo=constants.REPOS['rhel8_bos_ks']['name'],
        reposet=constants.REPOSET['rhel8_bos_ks'],
        releasever='8.4',  # should this value come from settings? yes
    ) # TODO: add appstream repo

    repo = default_sat.api.Repository(id=repo_id).read()
    repo.sync()
    repo = repo.read()

    os = (
        default_sat.api.OperatingSystem()
        .search(query={'search': 'family=Redhat and major=8 and minor=4'})[0]  # parametrize
        .read()
    )
    lce = (
        default_sat.api.LifecycleEnvironment(organization=module_manifest_org)
        .search(query={'search': f'name={constants.ENVIRONMENT}'})[0]
        .read()
    )
    cv = (
        default_sat.api.ContentView(
            organization=module_manifest_org,
            name=constants.DEFAULT_CV,
        )
        .search()[0]
        .read()
    )
    # TODO: publish/promote CV?

    hostgroup = default_sat.api.HostGroup(
        organization=[module_manifest_org],
        location=[module_location],
        architecture=default_architecture,
        domain=domain,
        content_source=provisioning_capsule.id,
        content_view=cv,
        kickstart_repository=repo,
        lifecycle_environment=lce,
        root_pass="changeme",
        operatingsystem=os,
        ptable=default_partitiontable,
        subnet=subnet,
        pxe_loader="PXELinux BIOS",
    ).create()
    # TODO: inspect HostGroup().read() method - nailgun.entity_mixins.NoSuchPathError

    hostgroup  # satisfy CI

    # TODO: add fdi to base template
    # ----- END OF SAT FIXTURE -----

    # run add-configure-vlan-interface on the host-to-be-provisioned
    VMBroker.execute(
        workflow="add-configure-vlan-iface",
        target_vlan_id=provisioning_network_vlan_id,
        target_host=rhel7_contenthost.name,
    )

    # run configure-pxe-boot-rhv on the host-to-be-provisioned
    VMBroker.execute(
        job_template="configure-pxe-boot-rhv",
        target_host=rhel7_contenthost.name,
        target_vlan_id=provisioning_network_vlan_id,
        pxeloader=provisioning_pxeloader,
    )
