from robottelo.datafactory import gen_string, valid_data_list
from robottelo.decorators import fixture, parametrize, tier2
from robottelo.config import settings
from nailgun import entities
from robottelo.constants import FOREMAN_PROVIDERS
import requests


@fixture(scope='module')
def module_ca_cert():
    return None if settings.rhev.ca_cert is None else \
                       requests.get(settings.rhev.ca_cert).content.decode()


@fixture(scope='module')
def module_org():
    return entities.Organization().create()


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


def add_rhev(session, version, module_ca_cert):
    rhev_url = settings.rhev.hostname
    username = settings.rhev.username
    password = settings.rhev.password
    datacenter = settings.rhev.datacenter
    name = gen_string('alpha')
    # Our currently used testing RHEV uses custom cert.
    # We need to manually specify it.
    # However, that means we're not testing the ability to automatically fill a
    # self-signed certificate upon clicking Load Datacenters / Test Connection.
    session.computeresource.create({
        'name': name,
        'provider': FOREMAN_PROVIDERS['rhev'],
        'provider_content.url': rhev_url,
        'provider_content.user': username,
        'provider_content.password': password,
        'provider_content.api4': version == 4,
        'provider_content.datacenter': datacenter,
        'provider_content.certification_authorities': module_ca_cert
    })
    found = session.computeresource.search(name)[0]
    assert found['Name'] == name
    assert session.computeresource.read(
        name)['provider_content']['api4'] == (version == 4)
    return found


@tier2
def test_positive_v3_wui_can_add_resource(session, module_ca_cert):
    """Create new RHEV Compute Resource using APIv3 and autoloaded cert

    :id: f75e994a-6da1-40a3-9685-42387388b300
    """
    with session:
        add_rhev(session, 3, module_ca_cert)


@tier2
def test_positive_v4_wui_can_add_resource(session, module_ca_cert):
    """Create new RHEV Compute Resource using APIv3 and autoloaded cert

    :id: f75e994a-6da1-40a3-9685-42387388b301
    """
    with session:
        add_rhev(session, 4, module_ca_cert)


def edit_rhev(session, module_org, cr, description, version):
    session.computeresource.edit(
        name=cr['Name'], values={'description': description})
    assert session.computeresource.read(
        cr['Name'])['description'] == description


@tier2
@parametrize('description', **valid_data_list('ui'))
def test_positive_v3_wui_can_edit_resource(
        session, module_org, module_ca_cert, description):
    """Edit a RHEV Compute Resource using APIv3

    :id: f75e994a-6da1-40a3-9685-42387388b302
    """
    with session:
        rhev3 = add_rhev(session, 3, module_ca_cert)
        edit_rhev(session, module_org, rhev3, description, 3)


@tier2
@parametrize('description', **valid_data_list('ui'))
def test_positive_v4_wui_can_edit_resource(
        session, module_org, module_ca_cert, description):
    """Edit a RHEV Compute Resource using APIv3

    :id: f75e994a-6da1-40a3-9685-42387388b303
    """
    with session:
        rhev4 = add_rhev(session, 4, module_ca_cert)
        edit_rhev(session, module_org, rhev4, description, 4)


def list_VMs(session, rhev, version):
    expected_vm_name = settings.rhev.vm_name
    vm = session.computeresource.list_vms(
            rhev['Name'], expected_vm_name)
    assert vm is not None


@tier2
def test_positive_v3_wui_virtual_machines_get_loaded(
        session, module_ca_cert):
    """List VMs using API v3

    :id: f75e994a-6da1-40a3-9685-42387388b304
    """
    with session:
        rhev3 = add_rhev(session, 3, module_ca_cert)
        list_VMs(session, rhev3, 3)


@tier2
def test_positive_v4_wui_virtual_machines_get_loaded(
        session, module_ca_cert):
    """List VMs using API v3

    :id: f75e994a-6da1-40a3-9685-42387388b305
    """
    with session:
        rhev4 = add_rhev(session, 4, module_ca_cert)
        list_VMs(session, rhev4, 4)


def switch_rhev_version(session, rhev, from_version):
    to_version = False if from_version == 4 else True
    orig_version = not to_version
    session.computeresource.edit(
        name=rhev['Name'], values={'provider_content.api4': to_version})
    assert session.computeresource.read(
        rhev['Name'])['provider_content']['api4'] == to_version
    session.computeresource.edit(
        name=rhev['Name'], values={'provider_content.api4': orig_version})


@tier2
def test_positive_v3_wui_can_switch_resource_to_v4(
        session, module_ca_cert):
    """Switch RHEV API v3 to v4
    Used API version should also be verified manually as described in
    https://url.corp.redhat.com/f7d3374

    :id: f75e994a-6da1-40a3-9685-42387388b306
    """
    with session:
        rhev3 = add_rhev(session, 3, module_ca_cert)
        switch_rhev_version(session, rhev3, 3)


@tier2
def test_positive_v4_wui_can_switch_resource_to_v3(
        session, module_ca_cert):
    """Switch RHEV API v4 to v3
    Used API version should also be verified manually as described in
    https://url.corp.redhat.com/f7d3374

    :id: f75e994a-6da1-40a3-9685-42387388b307
    """
    with session:
        rhev4 = add_rhev(session, 4, module_ca_cert)
        switch_rhev_version(session, rhev4, 4)


def vm_poweron(session, rhev):
    vm_name = settings.rhev.vm_name
    # power off first - nailgun can't do this,
    # it can only poweroff/on hosts, this is a plain unassociated VM
    session.computeresource.vm_poweroff(rhev['Name'], vm_name)
    assert not session.computeresource.vm_status(rhev['Name'], vm_name)
    session.computeresource.vm_poweron(rhev['Name'], vm_name)
    assert session.computeresource.vm_status(rhev['Name'], vm_name)


def vm_poweroff(session, rhev):
    vm_name = settings.rhev.vm_name
    # power off first - nailgun can't do this,
    # it can only poweroff/on hosts, this is a plain unassociated VM
    session.computeresource.vm_poweron(rhev['Name'], vm_name)
    assert session.computeresource.vm_status(rhev['Name'], vm_name)
    session.computeresource.vm_poweroff(rhev['Name'], vm_name)
    assert not session.computeresource.vm_status(rhev['Name'], vm_name)


@tier2
def test_positive_v3_wui_virtual_machines_can_be_powered_on(
        session, module_ca_cert):
    """Power on a machine on RHEV using APIv3

    :id: f75e994a-6da1-40a3-9685-42387388b308
    """
    with session:
        rhev3 = add_rhev(session, 3, module_ca_cert)
        vm_poweron(session, rhev3)


@tier2
def test_positive_v4_wui_virtual_machines_can_be_powered_on(
        session, module_ca_cert):
    """Power on a machine on RHEV using APIv4

    :id: f75e994a-6da1-40a3-9685-42387388b309
    """
    with session:
        rhev4 = add_rhev(session, 4, module_ca_cert)
        vm_poweron(session, rhev4)


@tier2
def test_positive_v3_wui_virtual_machines_can_be_powered_off(
        session, module_ca_cert):
    """Power off a machine on RHEV using APIv3

    :id: f75e994a-6da1-40a3-9685-42387388b30a
    """
    with session:
        rhev3 = add_rhev(session, 3, module_ca_cert)
        vm_poweroff(session, rhev3)


@tier2
def test_positive_v4_wui_virtual_machines_can_be_powered_off(
        session, module_ca_cert):
    """Power off a machine on RHEV using APIv4

    :id: f75e994a-6da1-40a3-9685-42387388b30b
    """
    with session:
        rhev4 = add_rhev(session, 4, module_ca_cert)
        vm_poweroff(session, rhev4)
