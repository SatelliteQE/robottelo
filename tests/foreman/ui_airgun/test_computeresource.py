from robottelo.datafactory import gen_string, valid_data_list
from robottelo.decorators import fixture, parametrize, tier2
from robottelo.config import settings
from nailgun import entities
from robottelo.constants import FOREMAN_PROVIDERS


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


@fixture(scope='module')
def module_rhev3(module_org):
    rhev_url = settings.rhev.hostname
    username = settings.rhev.username
    password = settings.rhev.password
    return entities.OVirtComputeResource(
        url=rhev_url, user=username, password=password,
        organization=[module_org], use_v4=False).create()


@fixture(scope='module')
def module_rhev4(module_org):
    rhev_url = settings.rhev.hostname
    username = settings.rhev.username
    password = settings.rhev.password
    return entities.OVirtComputeResource(
        url=rhev_url, user=username, password=password,
        organization=[module_org], use_v4=True).create()


@parametrize('name', **valid_data_list('ui'))
def test_positive_create_docker(session, name):
    docker_url = settings.docker.external_url
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['docker'],
            'provider_content.url': docker_url,
        })
        assert session.computeresource.search(name)[0]['Name'] == name


@parametrize('name', **valid_data_list('ui'))
def test_positive_create_ec2(session, name):
    ec2_access_key = settings.ec2.access_key
    ec2_secret_key = settings.ec2.secret_key
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['ec2'],
            'provider_content.access_key': ec2_access_key,
            'provider_content.secret_key': ec2_secret_key,
        })
        assert session.computeresource.search(name)[0]['Name'] == name


@parametrize('name', **valid_data_list('ui'))
def test_positive_create_libvirt(session, name):
    libvirt_url = settings.compute_resources.libvirt_hostname
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['libvirt'],
            'provider_content.url': libvirt_url,
            'provider_content.display_type': 'VNC',
            'provider_content.console_passwords': True,
        })
        assert session.computeresource.search(name)[0]['Name'] == name


@parametrize('name', **valid_data_list('ui'))
def test_positive_create_vmware(session, name):
    vmware_vcenter = settings.vmware.vcenter
    vmware_user = settings.vmware.username
    vmware_password = settings.vmware.password
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['vmware'],
            'provider_content.vcenter': vmware_vcenter,
            'provider_content.user': vmware_user,
            'provider_content.password': vmware_password,
        })
        assert session.computeresource.search(name)[0]['Name'] == name


@parametrize('name', **valid_data_list('ui'))
def test_positive_create_rhv(session, name):
    rhev_url = settings.rhev.hostname
    username = settings.rhev.username
    password = settings.rhev.password
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['rhev'],
            'provider_content.url': rhev_url,
            'provider_content.user': username,
            'provider_content.password': password,
        })
        assert session.computeresource.search(name)[0]['Name'] == name


def test_positive_rename(session):
    name = gen_string('alpha')
    ak_name = gen_string('alpha')
    docker_url = settings.docker.external_url
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['docker'],
            'provider_content.url': docker_url,
        })
        session.computeresource.edit(name, {
            'name': ak_name,
        })
        assert session.computeresource.search(ak_name)[0]['Name'] == ak_name


def test_positive_delete(session):
    name = gen_string('alpha')
    docker_url = settings.docker.external_url
    with session:
        session.computeresource.create({
            'name': name,
            'description': gen_string('alpha'),
            'provider': FOREMAN_PROVIDERS['docker'],
            'provider_content.url': docker_url,
        })
        session.computeresource.delete(name)
        assert not session.computeresource.search(name)


def add_rhev(session, version):
    rhev_url = settings.rhev.hostname
    username = settings.rhev.username
    password = settings.rhev.password
    name = gen_string('alpha')
    with session:
        session.computeresource.create({
            'name': name,
            'provider': FOREMAN_PROVIDERS['rhev'],
            'provider_content.url': rhev_url,
            'provider_content.user': username,
            'provider_content.password': password,
            'provider_content.api4': version == 4,
        })
        assert session.computeresource.search(name)[0]['Name'] == name
        assert session.computeresource.read(
            name)['provider_content']['api4'] == (version == 4)


@tier2
def test_positive_v3_wui_can_add_resource(session):
    """Create new RHEV Compute Resource using APIv3 and autoloaded cert

    :id: f75e994a-6da1-40a3-9685-42387388b300
    """
    add_rhev(session, 3)


@tier2
def test_positive_v4_wui_can_add_resource(session):
    """Create new RHEV Compute Resource using APIv3 and autoloaded cert

    :id: f75e994a-6da1-40a3-9685-42387388b301
    """
    add_rhev(session, 4)


def edit_rhev(session, module_org, cr, description, version):
    with session:
        session.computeresource.edit(
            name=cr.name, values={'description': description})
        assert session.computeresource.read(
            cr.name)['description'] == description


@tier2
@parametrize('description', **valid_data_list('ui'))
def test_positive_v3_wui_can_edit_resource(
        session, module_org, module_rhev3, description):
    """Edit a RHEV Compute Resource using APIv3

    :id: f75e994a-6da1-40a3-9685-42387388b302
    """
    edit_rhev(session, module_org, module_rhev3, description, 3)


@tier2
@parametrize('description', **valid_data_list('ui'))
def test_positive_v4_wui_can_edit_resource(
        session, module_org, module_rhev4, description):
    """Edit a RHEV Compute Resource using APIv3

    :id: f75e994a-6da1-40a3-9685-42387388b303
    """
    edit_rhev(session, module_org, module_rhev4, description, 4)


def list_VMs(session, rhev, version):
    expected_vm_name = settings.rhev.vm_name
    with session:
            vm = session.computeresource.list_vms(
                    rhev.name, expected_vm_name)
            assert vm is not None


@tier2
def test_positive_v3_wui_virtual_machines_get_loaded(
        session, module_rhev3):
    """List VMs using API v3

    :id: f75e994a-6da1-40a3-9685-42387388b304
    """
    list_VMs(session, module_rhev3, 3)


@tier2
def test_positive_v4_wui_virtual_machines_get_loaded(
        session, module_rhev4):
    """List VMs using API v3

    :id: f75e994a-6da1-40a3-9685-42387388b305
    """
    list_VMs(session, module_rhev4, 4)


def switch_rhev_version(session, rhev, from_version):
    to_version = False if from_version == 4 else True
    orig_version = not to_version
    with session:
        session.computeresource.edit(
            name=rhev.name, values={'provider_content.api4': to_version})
        assert session.computeresource.read(
            rhev.name)['provider_content']['api4'] == to_version
        entities.OVirtComputeResource(
                    id=rhev.id, use_v4=orig_version).update(['use_v4'])


@tier2
def test_positive_v3_wui_can_switch_resource_to_v4(
        session, module_rhev3):
    """Switch RHEV API v3 to v4
    Used API version should also be verified manually as described in
    https://url.corp.redhat.com/f7d3374

    :id: f75e994a-6da1-40a3-9685-42387388b306
    """
    switch_rhev_version(session, module_rhev3, 3)


@tier2
def test_positive_v4_wui_can_switch_resource_to_v3(
        session, module_rhev4):
    """Switch RHEV API v4 to v3
    Used API version should also be verified manually as described in
    https://url.corp.redhat.com/f7d3374

    :id: f75e994a-6da1-40a3-9685-42387388b307
    """
    switch_rhev_version(session, module_rhev4, 4)


def vm_poweron(session, rhev):
    vm_name = settings.rhev.vm_name
    with session:
            # power off first - nailgun can't do this,
            # it can only poweroff/on hosts, this is a plain unassociated VM
            session.computeresource.vm_poweroff(rhev.name, vm_name)
            assert not session.computeresource.vm_status(rhev.name, vm_name)
            session.computeresource.vm_poweron(rhev.name, vm_name)
            assert session.computeresource.vm_status(rhev.name, vm_name)


def vm_poweroff(session, rhev):
    vm_name = settings.rhev.vm_name
    with session:
            # power off first - nailgun can't do this,
            # it can only poweroff/on hosts, this is a plain unassociated VM
            session.computeresource.vm_poweron(rhev.name, vm_name)
            assert session.computeresource.vm_status(rhev.name, vm_name)
            session.computeresource.vm_poweroff(rhev.name, vm_name)
            assert not session.computeresource.vm_status(rhev.name, vm_name)


@tier2
def test_positive_v3_wui_virtual_machines_can_be_powered_on(
        session, module_rhev3):
    """Power on a machine on RHEV using APIv3

    :id: f75e994a-6da1-40a3-9685-42387388b308
    """
    vm_poweron(session, module_rhev3)


@tier2
def test_positive_v4_wui_virtual_machines_can_be_powered_on(
        session, module_rhev4):
    """Power on a machine on RHEV using APIv4

    :id: f75e994a-6da1-40a3-9685-42387388b309
    """
    vm_poweron(session, module_rhev4)


@tier2
def test_positive_v3_wui_virtual_machines_can_be_powered_off(
        session, module_rhev3):
    """Power off a machine on RHEV using APIv3

    :id: f75e994a-6da1-40a3-9685-42387388b30a
    """
    vm_poweroff(session, module_rhev3)


@tier2
def test_positive_v4_wui_virtual_machines_can_be_powered_off(
        session, module_rhev4):
    """Power off a machine on RHEV using APIv4

    :id: f75e994a-6da1-40a3-9685-42387388b30b
    """
    vm_poweroff(session, module_rhev4)
