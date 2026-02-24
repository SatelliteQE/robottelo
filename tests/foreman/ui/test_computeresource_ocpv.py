"""
:Requirement: Computeresource - OCP-V

:CaseAutomation: Automated

:CaseComponent: ComputeResources-OCP-V

:Team: Rocket

:CaseImportance: High
"""

from fauxfactory import gen_string
import pytest
from wait_for import wait_for

from robottelo.config import settings


@pytest.mark.e2e
@pytest.mark.on_premises_provisioning
@pytest.mark.parametrize('setting_update', ['destroy_vm_on_host_delete=True'], indirect=True)
def test_positive_userdata_image_provision_end_to_end(
    request,
    setting_update,
    module_ocpv_cr,
    module_ocpv_sat,
    module_org,
    module_location,
    module_ocpv_image,
    module_ocpv_hostgroup,
):
    """Provision a host on OpenShift Virtualization using image-based provisioning via UI.

    :id: a1b2c3d4-5e6f-4a5b-8c9d-0e1f2a3b4c5d

    :steps:
        1. Create OCP compute resource
        2. Create image for the compute resource
        3. Create userdata provisioning template and associate with OS
        4. Create hostgroup
        5. Via UI: Create host with hostgroup, deploy on OCP-V, image, and interfaces
        6. Wait for build status and verify host status is Installed
        7. Verify the VM power status and memory usage under the compute resource.

    :expectedresults: Host is provisioned successfully on OpenShift Virtualization via UI

    :Verifies: SAT-42060, SAT-41355
    """
    name = gen_string('alpha').lower()
    sat = module_ocpv_sat
    os = module_ocpv_image.os
    domain_name = module_ocpv_hostgroup.domain.read().name
    host_fqdn = f'{name}.{domain_name}'
    memory = '6144'
    value = int(memory) / 1024

    USERDATA_TEMPLATE = """\
    #cloud-config
    <%# Contact Foreman to confirm instance is built -%>
    phone_home:
      url: <%= foreman_url('built') %>
      post: []
      tries: 10
    """

    # Create userdata provisioning template via API
    template_kind = sat.api.TemplateKind().search(query={'search': 'name=user_data'})[0]
    userdata_template = sat.api.ProvisioningTemplate(
        name=gen_string('alpha'),
        organization=[module_org],
        location=[module_location],
        snippet=False,
        template_kind=template_kind,
        operatingsystem=[os],
        template=USERDATA_TEMPLATE,
    ).create()

    os.provisioning_template.append(userdata_template)
    os.update(['provisioning_template'])
    sat.api.OSDefaultTemplate(
        operatingsystem=os,
        provisioning_template=userdata_template,
        template_kind=template_kind,
    ).create()

    with module_ocpv_sat.ui_session() as session:
        session.organization.select(org_name=module_org.name)
        session.location.select(loc_name=module_location.name)
        session.host.create(
            {
                'host.name': name,
                'host.hostgroup': module_ocpv_hostgroup.name,
                'provider_content.virtual_machine.cpus': '2',
                'provider_content.virtual_machine.memory': memory,
                'provider_content.virtual_machine.startup': True,
                'provider_content.storage.storage_class': 'trident-nfs (csi.trident.netapp.io)',
                'provider_content.storage.size': 18,
                'provider_content.storage.bootable': True,
                'operating_system.architecture': f'{settings.ocpv.image_arch}',
                'operating_system.operating_system': module_ocpv_image.os.title,
                'provider_content.operating_system.provision_method': 'image',
                'operating_system.image': module_ocpv_image.image.name,
                'operating_system.root_password': gen_string('alpha').lower(),
                'interfaces.interface.ocpv_network': f'{settings.ocpv.network}',
            }
        )

        # Teardown: delete host via API
        host_api = sat.api.Host().search(query={'search': f'name="{host_fqdn}"'})
        if host_api:
            request.addfinalizer(host_api[0].delete)

        wait_for(
            lambda: (
                sat.api.Host().search(query={'search': f'name="{host_fqdn}"'})[0].build_status_label
                != 'Pending installation'
            ),
            timeout=1500,
            delay=10,
        )

        host = sat.api.Host().search(query={'search': f'name="{host_fqdn}"'})[0]
        assert host.name == host_fqdn
        assert host.build_status_label == 'Installed'

        assert (
            session.computeresource.search_virtual_machine(module_ocpv_cr.name, host.name)[0][
                'Power'
            ]
            == 'On'
        )
        # Power management actions work correctly (Power Off transitions the VM state)
        assert (
            session.computeresource.search_virtual_machine(module_ocpv_cr.name, host.name)[0][
                'Actions'
            ]
            == 'Power Off'
        )
        # Memory allocation matches the configured value
        assert (
            session.computeresource.search_virtual_machine(module_ocpv_cr.name, host.name)[0][
                'Memory'
            ]
            == f'{round(value)} GB'
        )
        # Test VM power management: power off the VM and verify the state changes accordingly
        # After power off, the VM should show 'Off' status and 'Power On' as the available action
        session.computeresource.vm_poweroff(module_ocpv_cr.name, host.name)
        assert (
            session.computeresource.search_virtual_machine(module_ocpv_cr.name, host.name)[0][
                'Power'
            ]
            == 'Off'
        )
        assert (
            session.computeresource.search_virtual_machine(module_ocpv_cr.name, host.name)[0][
                'Actions'
            ]
            == 'Power On'
        )
