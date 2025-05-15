"""Test for ProvisioningTemplates related Upgrade Scenario's

:Requirement: UpgradedSatellite

:CaseAutomation: Automated

:CaseComponent: ProvisioningTemplates

:Team: Rocket

:CaseImportance: High

"""

from box import Box
from fauxfactory import gen_alpha, gen_mac, gen_string
import pytest

from robottelo.config import settings
from robottelo.constants import (
    DEFAULT_ARCHITECTURE,
    DEFAULT_PTABLE,
    DEFAULT_PXE_TEMPLATE,
)
from robottelo.utils.shared_resource import SharedResource

provisioning_template_kinds = ['provision', 'PXEGrub', 'PXEGrub2', 'PXELinux', 'iPXE']
# provisioning_template_kinds = ['provision', 'PXEGrub', 'PXEGrub2', 'PXELinux']


@pytest.fixture
@pytest.mark.parametrize('pxe_loader', ['bios', 'uefi'], indirect=True)
def provisioning_templates_setup(
    content_upgrade_shared_satellite,
    pxe_loader,
    upgrade_action,
):
    """Verify that created host can read provisioning templates.

    :steps:
        1. Create host on Satellite and trying rendering provisioning templates.
        2. Upgrade the Satellite to the next or latest version.

    :expectedresults:
        1. Provisioning templates for host can be rendered before upgrading to new version.

    :parametrized: yes
    """
    target_sat = content_upgrade_shared_satellite
    with SharedResource(target_sat.hostname, upgrade_action, target_sat=target_sat) as sat_upgrade:
        test_name = f'provisioning_template_upgrade_{gen_alpha(length=8)}'
        org = target_sat.api.Organization(name=f'{test_name}_org').create()
        location = target_sat.api.Location(name=f'{test_name}_location').create()
        arch = (
            target_sat.api.Architecture()
            .search(query={'search': f'name="{DEFAULT_ARCHITECTURE}"'})[0]
            .read()
        )
        domain = target_sat.api.Domain().search(
            query={'search': f'name={target_sat.hostname.partition(".")[-1]}'}
        )[0]
        ptable = target_sat.api.PartitionTable().search(
            query={'search': f'name="{DEFAULT_PTABLE}"'}
        )[0]
        pxe_template = (
            target_sat.api.ProvisioningTemplate()
            .search(query={'search': DEFAULT_PXE_TEMPLATE})[0]
            .read()
        )
        os = (
            target_sat.api.OperatingSystem()
            .search(
                query={'search': f'name="{settings.supportability.content_hosts.default_os_name}"'}
            )[0]
            .read()
        )
        os.architecture.append(arch)
        os.ptable.append(ptable)
        os.provisioning_template.append(pxe_template)
        os.update(['architecture', 'ptable', 'provisioning_template'])
        host = target_sat.api.Host(
            organization=org,
            location=location,
            name=gen_string('alpha'),
            operatingsystem=os,
            architecture=arch,
            domain=domain,
            root_pass=settings.provisioning.host_root_password,
            ptable=ptable,
            pxe_loader=pxe_loader.pxe_loader,
            managed=False,
        ).create()

        for kind in provisioning_template_kinds:
            assert host.read_template(data={'template_kind': kind})

        sat_upgrade.ready()
        test_data = Box(
            {
                'provision_host_name': host.name,
                'pxe_loader': pxe_loader.pxe_loader,
                'target_sat': target_sat,
            }
        )
        target_sat._session = None
        yield test_data


@pytest.mark.parametrize('provisioning_templates_setup', ['bios', 'uefi'], indirect=True)
def test_post_scenario_provisioning_templates(
    provisioning_templates_setup,
    request,
):
    """Verify that pre-upgrade host and new host can read provisioning templates.

    :id: ef82143d-efef-49b2-9702-93d67ef6805e


    :steps:
        1. Postupgrade, verify provisioning templates rendering for host.
        2. Create a new host on Satellite and try rendering provisioning templates.

    :expectedresults:
        1. Provisioning templates for existing and new hosts can be rendered.

    :parametrized: yes
    """
    pxe_loader = provisioning_templates_setup.pxe_loader
    target_sat = provisioning_templates_setup.target_sat
    pre_upgrade_host = target_sat.api.Host().search(
        query={'search': f'name={provisioning_templates_setup.provision_host_name}'}
    )[0]
    request.addfinalizer(pre_upgrade_host.delete)
    org = target_sat.api.Organization(id=pre_upgrade_host.organization.id).read()
    location = target_sat.api.Location(id=pre_upgrade_host.location.id).read()
    domain = target_sat.api.Domain(id=pre_upgrade_host.domain.id).read()
    architecture = target_sat.api.Architecture(id=pre_upgrade_host.architecture.id).read()
    os = target_sat.api.OperatingSystem(id=pre_upgrade_host.operatingsystem.id).read()
    ptable = target_sat.api.PartitionTable(id=pre_upgrade_host.ptable.id).read()
    mac_address = gen_mac(multicast=False)

    for kind in provisioning_template_kinds:
        assert pre_upgrade_host.read_template(data={'template_kind': kind})

    new_host_name = gen_string('alpha')
    new_host = target_sat.api.Host(
        name=new_host_name,
        organization=org,
        location=location,
        architecture=architecture,
        domain=domain,
        mac=mac_address,
        operatingsystem=os,
        ptable=ptable,
        root_pass=settings.provisioning.host_root_password,
        pxe_loader=pxe_loader,
    ).create()
    request.addfinalizer(new_host.delete)

    for kind in provisioning_template_kinds:
        assert new_host.read_template(data={'template_kind': kind})
