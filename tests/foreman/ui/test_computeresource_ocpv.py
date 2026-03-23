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
from robottelo.constants import FOREMAN_PROVIDERS


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
    domain_name = module_ocpv_hostgroup.domain.read().name
    host_fqdn = f'{name}.{domain_name}'
    memory = '6144'
    memory_in_gb = int(memory) / 1024

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
                'operating_system.root_password': settings.provisioning.host_root_password,
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

        on_value = session.computeresource.search_virtual_machine(module_ocpv_cr.name, host.name)
        assert on_value[0]['Power'] == 'On'

        # Power management actions work correctly (Power Off transitions the VM state)
        assert on_value[0]['Actions'] == 'Power Off'

        # Memory allocation matches the configured value
        assert on_value[0]['Memory'] == f'{round(memory_in_gb)} GB'

        # Test VM power management: power off the VM and verify the state changes accordingly
        # After power off, the VM should show 'Off' status and 'Power On' as the available action
        session.computeresource.vm_poweroff(module_ocpv_cr.name, host.name)
        off_value = session.computeresource.search_virtual_machine(module_ocpv_cr.name, host.name)
        assert off_value[0]['Power'] == 'Off'
        assert off_value[0]['Actions'] == 'Power On'


@pytest.mark.e2e
def test_positive_cr_end_to_end(session, module_org, module_location, module_ocpv_sat):
    """Perform end-to-end testing for compute resource OpenShift Virtualization component.

    :id: c9654acc-2244-44d4-8e93-4d13262a39de

    :expectedresults: All expected CRUD actions finished successfully.
    """
    # Generate test data and create extra org/location for edit step
    cr_name = gen_string('alpha')
    new_cr_name = gen_string('alpha')
    description = gen_string('alpha')
    new_org = module_ocpv_sat.api.Organization().create()
    new_loc = module_ocpv_sat.api.Location().create()
    with session:
        # CREATE: Add OCP-V compute resource with provider settings
        session.computeresource.create(
            {
                'name': cr_name,
                'description': description,
                'provider': FOREMAN_PROVIDERS['ocp-v'],
                'provider_content.hostname': settings.ocpv.hostname,
                'provider_content.api_port': settings.ocpv.api_port,
                'provider_content.namespace': settings.ocpv.namespace,
                'provider_content.token': settings.ocpv.token,
                'provider_content.ca_cert': settings.ocpv.ca_cert,
                'organizations.resources.assigned': [module_org.name],
                'locations.resources.assigned': [module_location.name],
            }
        )
        # READ: Verify created compute resource shows correct values
        cr_values = session.computeresource.read(cr_name)
        assert cr_values['name'] == cr_name
        assert cr_values['description'] == description
        assert cr_values['provider'] == FOREMAN_PROVIDERS['ocp-v']
        assert cr_values['provider_content']['hostname'] == settings.ocpv.hostname
        assert cr_values['provider_content']['api_port'] == str(settings.ocpv.api_port)
        assert cr_values['provider_content']['namespace'] == settings.ocpv.namespace
        assert cr_values['organizations']['resources']['assigned'] == [module_org.name]
        assert cr_values['locations']['resources']['assigned'] == [module_location.name]
        # UPDATE: Rename CR and add another org/location
        session.computeresource.edit(
            cr_name,
            {
                'name': new_cr_name,
                'organizations.resources.assigned': [new_org.name],
                'locations.resources.assigned': [new_loc.name],
            },
        )
        assert not session.computeresource.search(cr_name)
        # Verify edit: new name and both original + new org/location assigned
        cr_values = session.computeresource.read(new_cr_name)
        assert cr_values['name'] == new_cr_name
        assert set(cr_values['organizations']['resources']['assigned']) == {
            module_org.name,
            new_org.name,
        }
        assert set(cr_values['locations']['resources']['assigned']) == {
            module_location.name,
            new_loc.name,
        }
        # DELETE: Remove compute resource and verify it no longer appears
        session.computeresource.delete(new_cr_name)
        assert not session.computeresource.search(new_cr_name)
