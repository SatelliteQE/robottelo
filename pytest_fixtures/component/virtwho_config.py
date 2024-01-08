import pytest

from robottelo.config import settings
from robottelo.utils.datafactory import gen_string
from robottelo.utils.virtwho import (
    deploy_configure_by_command,
    deploy_configure_by_script,
    get_configure_command,
    get_configure_command_option,
    get_guest_info,
)

LOGGEDOUT = 'Logged out.'


@pytest.fixture
def org_module(request, default_org, module_sca_manifest_org):
    if 'sca' in request.module.__name__.split('.')[-1]:
        org_module = module_sca_manifest_org
    else:
        org_module = default_org
    return org_module


@pytest.fixture
def org_session(request, session, session_sca):
    if 'sca' in request.module.__name__.split('.')[-1]:
        org_session = session_sca
    else:
        org_session = session
    return org_session


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
def form_data_ui(request, target_sat, org_module):
    hypervisor_type = request.module.__name__.split('.')[-1].split('_', 1)[-1]
    if 'esx' in hypervisor_type:
        form = {
            'debug': True,
            'interval': 'Every hour',
            'hypervisor_id': 'hostname',
            'hypervisor_type': settings.virtwho.esx.hypervisor_type,
            'hypervisor_content.server': settings.virtwho.esx.hypervisor_server,
            'hypervisor_content.username': settings.virtwho.esx.hypervisor_username,
            'hypervisor_content.password': settings.virtwho.esx.hypervisor_password,
        }
    elif 'hyperv' in hypervisor_type:
        form = {
            'debug': True,
            'interval': 'Every hour',
            'hypervisor_id': 'hostname',
            'hypervisor_type': settings.virtwho.hyperv.hypervisor_type,
            'hypervisor_content.server': settings.virtwho.hyperv.hypervisor_server,
            'hypervisor_content.username': settings.virtwho.hyperv.hypervisor_username,
            'hypervisor_content.password': settings.virtwho.hyperv.hypervisor_password,
        }
    elif 'kubevirt' in hypervisor_type:
        form = {
            'debug': True,
            'interval': 'Every hour',
            'hypervisor_id': 'hostname',
            'hypervisor_type': settings.virtwho.kubevirt.hypervisor_type,
            'hypervisor_content.kubeconfig': settings.virtwho.kubevirt.hypervisor_config_file,
        }
    elif 'libvirt' in hypervisor_type:
        form = {
            'debug': True,
            'interval': 'Every hour',
            'hypervisor_id': 'hostname',
            'hypervisor_type': settings.virtwho.libvirt.hypervisor_type,
            'hypervisor_content.server': settings.virtwho.libvirt.hypervisor_server,
            'hypervisor_content.username': settings.virtwho.libvirt.hypervisor_username,
        }
    elif 'nutanix' in hypervisor_type:
        form = {
            'debug': True,
            'interval': 'Every hour',
            'hypervisor_id': 'hostname',
            'hypervisor_type': settings.virtwho.ahv.hypervisor_type,
            'hypervisor_content.server': settings.virtwho.ahv.hypervisor_server,
            'hypervisor_content.username': settings.virtwho.ahv.hypervisor_username,
            'hypervisor_content.password': settings.virtwho.ahv.hypervisor_password,
            'hypervisor_content.prism_flavor': "Prism Element",
            'ahv_internal_debug': False,
        }
    return form


@pytest.fixture
def virtwho_config_cli(form_data_cli, target_sat):
    virtwho_config_cli = target_sat.cli.VirtWhoConfig.create(form_data_cli)['general-information']
    yield virtwho_config_cli
    target_sat.cli.VirtWhoConfig.delete({'name': virtwho_config_cli['name']})
    assert not target_sat.cli.VirtWhoConfig.exists(search=('name', form_data_cli['name']))


@pytest.fixture
def virtwho_config_api(form_data_api, target_sat):
    virtwho_config_api = target_sat.api.VirtWhoConfig(**form_data_api).create()
    yield virtwho_config_api
    virtwho_config_api.delete()
    assert not target_sat.api.VirtWhoConfig().search(
        query={'search': f"name={form_data_api['name']}"}
    )


@pytest.fixture
def virtwho_config_ui(form_data_ui, target_sat, org_session):
    name = gen_string('alpha')
    form_data_ui['name'] = name
    with org_session:
        org_session.virtwho_configure.create(form_data_ui)
        yield virtwho_config_ui
        org_session.virtwho_configure.delete(name)
        assert not org_session.virtwho_configure.search(name)


@pytest.fixture
def deploy_type_cli(
    request,
    org_module,
    form_data_cli,
    virtwho_config_cli,
    target_sat,
    default_location,
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
    elif deploy_type == "name":
        command = get_configure_command_option(deploy_type, virtwho_config_cli, org_module.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], debug=True, org=org_module.label
        )
    elif deploy_type == "organization-title":
        virtwho_config_cli['organization-title'] = org_module.title
        command = get_configure_command_option(deploy_type, virtwho_config_cli, org_module.name)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], debug=True, org=org_module.label
        )
    elif deploy_type == "location-id":
        virtwho_config_cli['location-id'] = default_location.id
        command = get_configure_command_option(deploy_type, virtwho_config_cli, org_module.name)
        print(command)
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data_cli['hypervisor-type'], debug=True, org=org_module.label
        )
    return hypervisor_name, guest_name


@pytest.fixture
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
    return hypervisor_name, guest_name


@pytest.fixture
def deploy_type_ui(
    request,
    org_module,
    form_data_ui,
    org_session,
    virtwho_config_ui,
    target_sat,
):
    deploy_type = request.param.lower()
    values = org_session.virtwho_configure.read(form_data_ui['name'])
    if "id" in deploy_type:
        command = values['deploy']['command']
        hypervisor_name, guest_name = deploy_configure_by_command(
            command, form_data_ui['hypervisor_type'], debug=True, org=org_module.label
        )
    elif "script" in deploy_type:
        script = values['deploy']['script']
        hypervisor_name, guest_name = deploy_configure_by_script(
            script, form_data_ui['hypervisor_type'], debug=True, org=org_module.label
        )
    return hypervisor_name, guest_name


@pytest.fixture
def delete_host(form_data_api, target_sat):
    guest_name, _ = get_guest_info(form_data_api['hypervisor_type'])
    results = target_sat.api.Host().search(query={'search': guest_name})
    if results:
        target_sat.api.Host(id=results[0].read_json()['id']).delete()
