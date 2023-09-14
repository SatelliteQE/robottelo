import pytest

from robottelo.config import settings
from robottelo.utils.datafactory import gen_string
from robottelo.utils.virtwho import deploy_configure_by_command
from robottelo.utils.virtwho import deploy_configure_by_script
from robottelo.utils.virtwho import get_configure_command
from robottelo.utils.virtwho import get_guest_info

LOGGEDOUT = 'Logged out.'


@pytest.fixture()
def org_module(request, default_org, module_sca_manifest_org):
    if 'sca' in request.module.__name__.split('.')[-1]:
        org_module = module_sca_manifest_org
    else:
        org_module = default_org
    return org_module


@pytest.fixture()
def form_data_cli(request, target_sat, org_module):
    hypervisor_type = request.module.__name__.split('.')[-1].split('_', 1)[-1]
    if 'esx' in hypervisor_type:
        form = {
            'name': gen_string('alpha'),
            'debug': 1,
            'interval': '60',
            'hypervisor-id': 'hostname',
            'hypervisor-type': settings.virtwho.esx.hypervisor_type,
            'hypervisor-server': settings.virtwho.esx.hypervisor_server,
            'organization-id': org_module.id,
            'filtering-mode': 'none',
            'satellite-url': target_sat.hostname,
            'hypervisor-username': settings.virtwho.esx.hypervisor_username,
            'hypervisor-password': settings.virtwho.esx.hypervisor_password,
        }
    elif 'hyperv' in hypervisor_type:
        form = {
            'name': gen_string('alpha'),
            'debug': 1,
            'interval': '60',
            'hypervisor-id': 'hostname',
            'hypervisor-type': settings.virtwho.hyperv.hypervisor_type,
            'hypervisor-server': settings.virtwho.hyperv.hypervisor_server,
            'organization-id': org_module.id,
            'filtering-mode': 'none',
            'satellite-url': target_sat.hostname,
            'hypervisor-username': settings.virtwho.hyperv.hypervisor_username,
            'hypervisor-password': settings.virtwho.hyperv.hypervisor_password,
        }
    elif 'kubevirt' in hypervisor_type:
        form = {
            'name': gen_string('alpha'),
            'debug': 1,
            'interval': '60',
            'hypervisor-id': 'hostname',
            'hypervisor-type': settings.virtwho.kubevirt.hypervisor_type,
            'organization-id': org_module.id,
            'filtering-mode': 'none',
            'satellite-url': target_sat.hostname,
            'kubeconfig-path': settings.virtwho.kubevirt.hypervisor_config_file,
        }
    elif 'libvirt' in hypervisor_type:
        form = {
            'name': gen_string('alpha'),
            'debug': 1,
            'interval': '60',
            'hypervisor-id': 'hostname',
            'hypervisor-type': settings.virtwho.libvirt.hypervisor_type,
            'hypervisor-server': settings.virtwho.libvirt.hypervisor_server,
            'organization-id': org_module.id,
            'filtering-mode': 'none',
            'satellite-url': target_sat.hostname,
            'hypervisor-username': settings.virtwho.libvirt.hypervisor_username,
        }
    elif 'nutanix' in hypervisor_type:
        form = {
            'name': gen_string('alpha'),
            'debug': 1,
            'interval': '60',
            'hypervisor-id': 'hostname',
            'hypervisor-type': settings.virtwho.ahv.hypervisor_type,
            'hypervisor-server': settings.virtwho.ahv.hypervisor_server,
            'organization-id': org_module.id,
            'filtering-mode': 'none',
            'satellite-url': target_sat.hostname,
            'hypervisor-username': settings.virtwho.ahv.hypervisor_username,
            'hypervisor-password': settings.virtwho.ahv.hypervisor_password,
            'prism-flavor': settings.virtwho.ahv.prism_flavor,
            'ahv-internal-debug': 'false',
        }
    return form


@pytest.fixture()
def form_data_api(request, target_sat, org_module):
    hypervisor_type = request.module.__name__.split('.')[-1].split('_', 1)[-1]
    if 'esx' in hypervisor_type:
        form = {
            'name': gen_string('alpha'),
            'debug': 1,
            'interval': '60',
            'hypervisor_id': 'hostname',
            'hypervisor_type': settings.virtwho.esx.hypervisor_type,
            'hypervisor_server': settings.virtwho.esx.hypervisor_server,
            'organization_id': org_module.id,
            'filtering_mode': 'none',
            'satellite_url': target_sat.hostname,
            'hypervisor_username': settings.virtwho.esx.hypervisor_username,
            'hypervisor_password': settings.virtwho.esx.hypervisor_password,
        }
    elif 'hyperv' in hypervisor_type:
        form = {
            'name': gen_string('alpha'),
            'debug': 1,
            'interval': '60',
            'hypervisor_id': 'hostname',
            'hypervisor_type': settings.virtwho.hyperv.hypervisor_type,
            'hypervisor_server': settings.virtwho.hyperv.hypervisor_server,
            'organization_id': org_module.id,
            'filtering_mode': 'none',
            'satellite_url': target_sat.hostname,
            'hypervisor_username': settings.virtwho.hyperv.hypervisor_username,
            'hypervisor_password': settings.virtwho.hyperv.hypervisor_password,
        }
    elif 'kubevirt' in hypervisor_type:
        form = {
            'name': gen_string('alpha'),
            'debug': 1,
            'interval': '60',
            'hypervisor_id': 'hostname',
            'hypervisor_type': settings.virtwho.kubevirt.hypervisor_type,
            'organization_id': org_module.id,
            'filtering_mode': 'none',
            'satellite_url': target_sat.hostname,
            'kubeconfig_path': settings.virtwho.kubevirt.hypervisor_config_file,
        }
    elif 'libvirt' in hypervisor_type:
        form = {
            'name': gen_string('alpha'),
            'debug': 1,
            'interval': '60',
            'hypervisor_id': 'hostname',
            'hypervisor_type': settings.virtwho.libvirt.hypervisor_type,
            'hypervisor_server': settings.virtwho.libvirt.hypervisor_server,
            'organization_id': org_module.id,
            'filtering_mode': 'none',
            'satellite_url': target_sat.hostname,
            'hypervisor_username': settings.virtwho.libvirt.hypervisor_username,
        }
    elif 'nutanix' in hypervisor_type:
        form = {
            'name': gen_string('alpha'),
            'debug': 1,
            'interval': '60',
            'hypervisor_id': 'hostname',
            'hypervisor_type': settings.virtwho.ahv.hypervisor_type,
            'hypervisor_server': settings.virtwho.ahv.hypervisor_server,
            'organization_id': org_module.id,
            'filtering_mode': 'none',
            'satellite_url': target_sat.hostname,
            'hypervisor_username': settings.virtwho.ahv.hypervisor_username,
            'hypervisor_password': settings.virtwho.ahv.hypervisor_password,
            'prism_flavor': settings.virtwho.ahv.prism_flavor,
            'ahv_internal_debug': 'false',
        }
    return form


@pytest.fixture()
def virtwho_config_cli(form_data_cli, target_sat):
    virtwho_config_cli = target_sat.cli.VirtWhoConfig.create(form_data_cli)['general-information']
    yield virtwho_config_cli
    target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config_cli['name']})
    assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data_cli['name']))


@pytest.fixture()
def virtwho_config_api(form_data_api, target_sat):
    virtwho_config_api = target_sat.api.VirtWhoConfig(**form_data_api).create()
    yield virtwho_config_api
    virtwho_config_api.delete()
    assert not target_sat.api.VirtWhoConfig().search(
        query={'search': f"name={form_data_api['name']}"}
    )


@pytest.fixture()
def deploy_type_cli(
    request,
    org_module,
    form_data_cli,
    virtwho_config_cli,
    target_sat,
):
    deploy_type = request.param.lower()
    assert virtwho_config_cli['status'] == 'No Report Yet'
    if "id" in deploy_type:
        command = get_configure_command(virtwho_config_cli['id'], org_module.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], debug=True, org=org_module.label
        )
    elif "script" in deploy_type:
        script = target_sat.cli.VirtWhoConfig.fetch(
            {'id': virtwho_config_cli['id']}, output_format='base'
        )
        hypervisor_name, guest_name = deploy_configure_by_script(
            script, form_data_cli['hypervisor-type'], debug=True, org=org_module.label
        )
    yield hypervisor_name, guest_name


@pytest.fixture()
def deploy_type_api(
    request,
    org_module,
    form_data_api,
    virtwho_config_api,
    target_sat,
):
    deploy_type = request.param.lower()
    assert virtwho_config_api.status == 'unknown'
    if "id" in deploy_type:
        command = get_configure_command(virtwho_config_api.id, org_module.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data_api['hypervisor_type'], debug=True, org=org_module.label
        )
    elif "script" in deploy_type:
        script = virtwho_config_api.deploy_script()
        hypervisor_name, guest_name = deploy_configure_by_script(
            script['virt_who_config_script'],
            form_data_api['hypervisor_type'],
            debug=True,
            org=org_module.label,
        )
    yield hypervisor_name, guest_name


@pytest.fixture()
def delete_host(form_data, target_sat):
    guest_name, _ = get_guest_info(form_data['hypervisor_type'])
    results = target_sat.api.Host().search(query={'search': guest_name})
    if results:
        target_sat.api.Host(id=results[0].read_json()['id']).delete()
